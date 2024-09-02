import os
import json
import subprocess
from pydriller import Git
from copy import deepcopy

# copied from the 'diffconfig' script shared in the linux reporsitory
# returns a dictionary of name/value pairs for config items in the file
def readconfig(config_file):
    d = {}
    for line in config_file:
        line = line[:-1]
        if line[:7] == "CONFIG_":
            name, val = line[7:].split("=", 1)
            d[name] = val
        if line[-11:] == " is not set":
            d[line[9:-11]] = "n"
    return d

def save_to_dot_config(kernel_config, save_dir, special_code:str) :
    with open(os.path.join(save_dir,".config_{}".format(special_code)),"w") as f :
        f.write(kernel_config)
    with open(os.path.join(save_dir,".config_{}_for_comparison".format(special_code)),"w") as f :
        f.write(kernel_config)

def prepare_for_data_point(save_dir,data_path,special_code) :
    # load bug data
    if os.path.exists(os.path.join(data_path,"original_data.json")) :
        with open(os.path.join(data_path,"original_data.json"),"r") as f :
            bug_data = json.load(f)
    else :
        with open(os.path.join(data_path + ".json"),"r") as f :
            bug_data = json.load(f)
    # get kernel config
    kernel_config_data = bug_data["crashes"][0]["kernel-config-data"]
    save_to_dot_config(kernel_config_data,save_dir,special_code)

def read_file(config_file_path) :
    with open(config_file_path,"r") as f :
        lines = f.readlines()
    return lines

def add_line_to_file(line_list, line) :
    line_list.append(line)

def remove_line_from_file(line_list,line) :
    line_key,line_value = line.split("=")
    found = False
    final_index = -1
    for index,ele in enumerate(line_list) :
        if line_key in ele :
            # Case A - CONFIG_BLAH is not set
            if "{} is not set".format(line_key) in ele :
                return
            # Case B - CONFIG_BLAH=...
            if "{}=".format(line_key) in ele :
                found = True
                final_index = index
                break
    assert(found)
    del line_list[final_index]

def replace_line_in_file(line_list,old_line,new_line) :
    found = False
    final_index = -1
    for index,ele in enumerate(line_list) :
        if old_line in ele :
            found = True
            final_index = index
            break
    assert(found)
    line_list[final_index] = new_line

def add_argument_to_config_cmdline(old_config_line_list,
                                old_config_dict,
                                new_config_dict,
                                new_arguments) :
    config_key = "CONFIG_CMDLINE"
    old_value = old_config_dict[config_key.replace("CONFIG_","")].strip()
    old_line = config_key + "=" + old_value

    new_value = old_value[:-1] + " " + new_arguments + "\""
    new_line = config_key + "=" + new_value + "\n"

    replace_line_in_file(old_config_line_list,old_line,new_line)

def make_changes_using_diff_file(old_config_line_list,
                                old_config_dict,
                                new_config_dict,
                                diff_file_path) :
    
    with open(diff_file_path,"r") as f :
        diff_lines = f.readlines()

        for line in diff_lines :
            line = line.strip()

            if len(line) == 0 :
                continue

            if line[0] == "-" :
                # line to be removed
                old_config_key = "CONFIG_" + line[1:].split(" ")[0]
                old_value = old_config_dict[old_config_key.replace("CONFIG_","")]
                old_line = old_config_key + "=" + old_value
                remove_line_from_file(old_config_line_list,old_line)
            
            elif line[0] == "+" :
                # line to be added
                new_config_key = "CONFIG_" + line[1:].split(" ")[0]
                new_value = new_config_dict[new_config_key.replace("CONFIG_","")]
                new_line = new_config_key + "=" + new_value + "\n"
                add_line_to_file(old_config_line_list,new_line)
            
            elif " -> " in line :
                # line to be modified
                config_key = "CONFIG_" + line.split(" ")[0]
                if config_key == "CONFIG_CMDLINE" :
                    # skip
                    pass
                else :
                    old_value = old_config_dict[config_key.replace("CONFIG_","")]
                    new_value = new_config_dict[config_key.replace("CONFIG_","")]
                    old_line = config_key+"="+old_value
                    new_line = config_key+"="+new_value+"\n"
                    replace_line_in_file(old_config_line_list,old_line,new_line)

def make_changes_to_config_file(kasan_config_file_path,
                                kmsan_config_file_path) :
    """ Convert the KASAN config file to the KMSAN config file. """
    kasan_file_dict = readconfig(open(kasan_config_file_path))
    kasan_file = read_file(kasan_config_file_path)

    kmsan_file_dict = readconfig(open(kmsan_config_file_path))
    kmsan_file = read_file(kmsan_config_file_path)

    # Remove KASAN related fields
    KASAN_diff_path = os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs/KASAN_diff.txt")
    make_changes_using_diff_file(old_config_line_list=kasan_file,
                                old_config_dict=kasan_file_dict,
                                new_config_dict=kmsan_file_dict,
                                diff_file_path=KASAN_diff_path)
    # Remove kasan related fields
    kasan_diff_path = os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs/kasan_diff.txt")
    make_changes_using_diff_file(old_config_line_list=kasan_file,
                                old_config_dict=kasan_file_dict,
                                new_config_dict=kmsan_file_dict,
                                diff_file_path=kasan_diff_path)

    # Add KMSAN related fields
    KMSAN_diff_path = os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs/KMSAN_diff.txt")
    make_changes_using_diff_file(old_config_line_list=kasan_file,
                                old_config_dict=kasan_file_dict,
                                new_config_dict=kmsan_file_dict,
                                diff_file_path=KMSAN_diff_path)
    # Add kmsan related fields
    kmsan_diff_path = os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs/kmsan_diff.txt")
    make_changes_using_diff_file(old_config_line_list=kasan_file,
                                old_config_dict=kasan_file_dict,
                                new_config_dict=kmsan_file_dict,
                                diff_file_path=kmsan_diff_path)

    # Add kmsan.panic=1 argument to the CONFIG_CMDLINE
    add_argument_to_config_cmdline(old_config_line_list=kasan_file,
                                old_config_dict=kasan_file_dict,
                                new_config_dict=kmsan_file_dict,
                                new_arguments="kmsan.panic=1")
    
    return kasan_file


# difference grepping for kmsan
# python3 ./diffconfig os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs/.config_1") os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs/.config_2") | grep "kmsan" > os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs/kmsan_diff.txt")

def main() :

    # Important note - KMSAN needs the clang compiler (it does not work with GCC)
    # grep -r "\"title\": \"KMSAN:" os.path.join(os.getenv("KGYM_PATH"),"seeds_folder")
    # grep -r "\"title\": \"KMSAN:" os.getenv("FIXED_DUMP_PATH")

    # grep -r "\"title\": \"KASAN:" os.path.join(os.getenv("KGYM_PATH"),"seeds_folder")
    # grep -r "\"title\": \"KASAN:" os.getenv("FIXED_DUMP_PATH")
    
    # linux version 5.10.0 - KASAN data point
    bug_id = "f5697a2cc8cc739814a87d3755258160e812c9dd"
    prepare_for_data_point(save_dir=os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs"), data_path=os.path.join(os.getenv("FIXED_DUMP_PATH"),"{}".format(bug_id)), special_code="1")

    # linux version 6.3.0 - KMSAN data point
    bug_id = "a2236e7dace23c5338f82242e0d3844ee3ac3e18"
    prepare_for_data_point(save_dir=os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs"), data_path=os.path.join(os.getenv("FIXED_DUMP_PATH"),"{}".format(bug_id)), special_code="2")

    kasan_config_file_path = os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs/.config_1")
    kmsan_config_file_path = os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs/.config_2")
    kasan_to_kmsan_file = make_changes_to_config_file(kasan_config_file_path,kmsan_config_file_path)

    with open(kasan_config_file_path + "_modified", "w") as f :
        f.writelines(kasan_to_kmsan_file)

    # command to run to check the difference
    # python3 ./diffconfig os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs/.config_1") os.path.join(os.getenv("KGYM_PATH"),"compare_two_configs/.config_1_modified")

    return

if __name__ == '__main__' :
    main()