from typing import List
from copy import deepcopy
import os
import json

class BaseConfigConvertor() :

    def __init__(self) :
        self.list_of_changes = []

    # copied from the 'diffconfig' script shared in the linux reporsitory
    # returns a dictionary of name/value pairs for config items in the file
    def readconfig(self,config_file):
        if type(config_file) == str :
            config_file = config_file.split("\n")
            config_file = [ele+"\n" for ele in config_file]
        d = {}
        for line in config_file:
            line = line[:-1]
            if line[:7] == "CONFIG_":
                name, val = line[7:].split("=", 1)
                d[name] = val
            if line[-11:] == " is not set":
                d[line[9:-11]] = "n"
        return d

    def read_file(self,config_file_path) :
        with open(config_file_path,"r") as f :
            lines = f.readlines()
        return lines
    
    def add_line_to_file(self,line_list, line) :
        if line[-1] != "\n" :
            line += "\n"
        line_list.append(line)
        self.list_of_changes.append("+" + line.split("=")[0] + " " + line.split("=")[1].strip())

    def remove_line_from_file(self,line_list,line) :
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
        self.list_of_changes.append("-" + line.split("=")[0] + " " + line.split("=")[1])

    def replace_line_in_file(self,line_list,line_key,old_value,new_value) :
        found = False
        final_index = -1
        for index,ele in enumerate(line_list) :
            # Case A - CONFIG_BLAH is not set
            if "{} is not set".format(line_key) in ele :
                found = True
                final_index = index
                break
            # Case B - CONFIG_BLAH=...
            elif "{}={}".format(line_key,old_value) in ele :
                found = True
                final_index = index
                break
        assert(found)
        if new_value[-1] != "\n" :
            new_value += "\n"
        line_list[final_index] = line_key+"="+new_value
        self.list_of_changes.append(line_key + " " + old_value + " -> " + new_value.strip())

    def remove_argument_from_config_cmdline(self, 
                                        old_config_line_list,
                                        old_config_dict,
                                        paramater_match) :
        config_key = "CONFIG_CMDLINE"
        old_value = old_config_dict[config_key.replace("CONFIG_","")].strip()
        old_value_list = old_value[1:-1].split(" ")

        new_value_list = []
        for ele in old_value_list :
            if ("=" not in ele) or (ele.find("=") != ele.rfind("=")) :
                # skip complex arguments with no '=' or more than one '='
                continue
            key,value = ele.split("=")
            if paramater_match in key :
                # if there is a match in this element
                continue
            else :
                new_value_list.append(ele)

        new_value = "\""
        for ele in new_value_list :
            new_value += ele + " "
        if new_value[-1] == " " :
            new_value = new_value[:-1]
        new_value += "\""
        self.replace_line_in_file(old_config_line_list,config_key,old_value,new_value)

    def add_argument_to_config_cmdline(self,
                                old_config_line_list,
                                old_config_dict,
                                new_arguments) :
        config_key = "CONFIG_CMDLINE"
        old_value = old_config_dict[config_key.replace("CONFIG_","")].strip()
        new_value = old_value[:-1] + " " + new_arguments + "\""
        self.replace_line_in_file(old_config_line_list,config_key,old_value,new_value)

    def make_changes_using_diff_line(self,
                                old_config_line_list:list,
                                old_config_dict:dict,
                                new_config_dict:dict,
                                diff_line) :
        if diff_line[0] == "-" :
            # line to be removed
            old_config_key = "CONFIG_" + diff_line[1:].split(" ")[0]
            old_value = old_config_dict[old_config_key.replace("CONFIG_","")]
            old_line = old_config_key + "=" + old_value
            self.remove_line_from_file(old_config_line_list,old_line)
        
        elif diff_line[0] == "+" :
            # line to be added
            new_config_key = "CONFIG_" + diff_line[1:].split(" ")[0]
            new_value = new_config_dict[new_config_key.replace("CONFIG_","")]
            new_line = new_config_key + "=" + new_value + "\n"
            self.add_line_to_file(old_config_line_list,new_line)
        
        elif " -> " in diff_line :
            # line to be modified
            config_key = "CONFIG_" + diff_line.split(" ")[0]
            if config_key == "CONFIG_CMDLINE" :
                # skip
                pass
            else :
                old_value = old_config_dict[config_key.replace("CONFIG_","")]
                new_value = new_config_dict[config_key.replace("CONFIG_","")]
                self.replace_line_in_file(old_config_line_list,config_key,old_value,new_value)

    def make_changes_using_diff_file(self,
                                old_config_line_list,
                                old_config_dict,
                                new_config_dict,
                                diff_file_path) :
    
        with open(diff_file_path,"r") as f :
            diff_lines = f.readlines()

            for line in diff_lines :
                line = line.strip()

                if len(line) == 0 :
                    continue

                self.make_changes_using_diff_line(old_config_line_list,old_config_dict,new_config_dict,line)

    def get_kernel_config(self,data_path) :

        if data_path.endswith(".json") :
            data_path = data_path[:-5]

        # load bug data
        if os.path.exists(os.path.join(data_path,"original_data.json")) :
            with open(os.path.join(data_path,"original_data.json"),"r") as f :
                bug_data = json.load(f)
        else :
            with open(os.path.join(data_path + ".json"),"r") as f :
                bug_data = json.load(f)
        # get kernel config
        kernel_config_data = bug_data["crashes"][0]["kernel-config-data"]
        return kernel_config_data

    def reset_list_of_changes(self) :
        self.list_of_changes = []

    def convert_config_file_to_config_list(self) :
    
        return
    
    # def change_compiler_to_clang(self,orig_file) :
    #     orig_dict = self.readconfig(orig_file)
    #     if orig_dict.get("CC_IS_CLANG",-1) == "y" :
    #         # compiler is already clang
    #         return
    #     else :
    #         self.replace_line_in_file(orig_file,"CONFIG_CC_IS_CLANG","n","y")
    #         self.replace_line_in_file(orig_file,"CONFIG_CC_VERSION_TEXT","","Debian clang version 15.0.7")
    #         self.replace_line_in_file(orig_file,"CONFIG_CLANG_VERSION","","150007")
    #     return

    def verify_with_convertor(self, file_path, src_path, verifier, type) :
        """ Verify that all the jobs have the correct config file as per the convertor. """

        with open(file_path,"r") as f :
            job_data = json.load(f)

        job_list = []
        bug_list = []
        for job in job_data["jobs"] :
            if job["job_id"] and job["type"]==type :
                job_list.append(job["job_id"].replace("\"",""))
                bug_list.append(job["bug_id"])

        all_correct = True
        for job,bug in zip(job_list,bug_list) :
            config_path = os.path.join(src_path,job,"0_kbuilder_kernel.config")
            if not os.path.exists(config_path) :
                continue
            with open(config_path,"r") as f :
                config_text = f.read()
                ans = verifier.check_config_changes(config_file=config_text)
                if not ans :
                    all_correct = False
                    print("Config for Bug ID {} : Job ID {} is not correct".format(bug,job))
        if all_correct :
            print("All correct")

class RemoveKASAN(BaseConfigConvertor) :

    def __init__(self):
        super().__init__()

    def find_KASAN_related_config_values(self,config_dict) :
        """Find all the config values related to KASAN. """
        config_list = []
        for key,value in config_dict.items() :
            if "KASAN" in key.split("_") :
                config_list.append((key,value))
        return config_list
    
    def remove_KASAN_configurations(self, KASAN_keys,orig_file) :
        for info in KASAN_keys :
            key = info[0]
            value = info[1]
            line = "CONFIG_" + key + "=" + value
            self.remove_line_from_file(orig_file,line)
        # explicit config entry that disables KASAN
        self.add_line_to_file(orig_file,"CONFIG_KASAN=n")

    def change_config_file(self,orig_file:List[str]) :
        self.reset_list_of_changes()
        orig_config_dict = self.readconfig(deepcopy(orig_file))
        all_KASAN_keys = self.find_KASAN_related_config_values(orig_config_dict)
        self.remove_KASAN_configurations(all_KASAN_keys,orig_file)
        complete_config_file = "".join(orig_file)
        return complete_config_file, self.list_of_changes
    
    def change_config_file_for_bug(self, data_path, bug_id:str) :
        changed_flag = False
        config_file = self.get_kernel_config(os.path.join(data_path,bug_id))

        # check if KASAN is even enabled
        config_dict = self.readconfig(deepcopy(config_file))
        if config_dict.get("KASAN",-1) == "n":
            # KASAN is already disabled
            return config_file, changed_flag, []

        config_file_lines = config_file.split("\n")
        config_file_lines = [ele+"\n" for ele in config_file_lines]
        new_config_file, list_of_changes = self.change_config_file(deepcopy(config_file_lines))
        changed_flag = True
        return new_config_file, changed_flag, list_of_changes

    def check_config_changes(self, config_file) :
        config_dict = self.readconfig(deepcopy(config_file))
        try :
            assert(config_dict["KASAN"]=="n")
            return True
        except Exception as e :
            return False 

    def verify_with_RemoveKASAN(self, file_path, src_path) :
        self.verify_with_convertor(file_path, src_path, verifier=self, type="without_KASAN")

class VanillaKASAN(BaseConfigConvertor) :
    """ Not a convertor. Just a verifier for vanilla KASAN bugs. """
    def check_config_changes(self, config_file) :
        config_dict = self.readconfig(deepcopy(config_file))
        try :
            assert(config_dict["KASAN"]=="y")
            return True
        except Exception as e :
            return False

    def verify_with_VanillaKASAN(self, file_path, src_path) :
        self.verify_with_convertor(file_path, src_path, verifier=self, type="vanilla")

class RemoveKMSAN(BaseConfigConvertor) :

    def __init__(self):
        super().__init__()

    def find_KMSAN_related_config_values(self,config_dict) :
        """Find all the config values related to KMSAN. """
        config_list = []
        for key,value in config_dict.items() :
            if "KMSAN" in key.split("_") :
                config_list.append((key,value))
        return config_list
    
    def remove_KMSAN_configurations(self, KMSAN_keys,orig_file) :
        for info in KMSAN_keys :
            key = info[0]
            value = info[1]
            line = "CONFIG_" + key + "=" + value
            self.remove_line_from_file(orig_file,line)
        # explicit config entry that disables KMSAN
        self.add_line_to_file(orig_file,"CONFIG_KMSAN=n")

    def change_config_file(self,orig_file:List[str]) :
        self.reset_list_of_changes()
        orig_config_dict = self.readconfig(deepcopy(orig_file))
        all_KMSAN_keys = self.find_KMSAN_related_config_values(orig_config_dict)
        self.remove_KMSAN_configurations(all_KMSAN_keys,orig_file)
        self.remove_argument_from_config_cmdline(orig_file,orig_config_dict,paramater_match="kmsan")
        complete_config_file = "".join(orig_file)
        return complete_config_file, self.list_of_changes
    
    def change_config_file_for_bug(self, data_path, bug_id:str) :
        changed_flag = False
        config_file = self.get_kernel_config(os.path.join(data_path,bug_id))

        # check if KMSAN is even enabled
        config_dict = self.readconfig(deepcopy(config_file))
        if config_dict.get("KMSAN",-1) == "n":
            # KMSAN is already disabled
            return config_file, changed_flag, []

        config_file_lines = config_file.split("\n")
        config_file_lines = [ele+"\n" for ele in config_file_lines]
        new_config_file, list_of_changes = self.change_config_file(deepcopy(config_file_lines))
        changed_flag = True
        return new_config_file, changed_flag, list_of_changes

    def check_config_changes(self, config_file) :
        config_dict = self.readconfig(deepcopy(config_file))
        try :
            assert(config_dict["KMSAN"]=="n")            
            assert("kmsan.panic=1" not in  config_dict["CMDLINE"])
            return True
        except Exception as e :
            return False 

    def verify_with_RemoveKMSAN(self, file_path, src_path) : 
        self.verify_with_convertor(file_path, src_path, verifier=self, type="without_KMSAN")

class AddKMSAN(BaseConfigConvertor) :

    def __init__(self):
        super().__init__()
        self.default_kmsan_dict = {
            "CONFIG_HAVE_ARCH_KMSAN"  : "y",
            "CONFIG_HAVE_KMSAN_COMPILER" : "y",
            "CONFIG_HAVE_KMSAN_PARAM_RETVAL" : "y",
            "CONFIG_KMSAN" : "y",
            "CONFIG_KMSAN_CHECK_PARAM_RETVAL" : "y"
        }

    def add_KMSAN_configurations(self, orig_file) :
        # CHECK FOR THIS !
        # -KASAN_SHADOW_OFFSET 0xdffffc0000000000
        orig_config_dict = self.readconfig(orig_file)
        for key,value in self.default_kmsan_dict.items() :
            # check if it already exists in the config file
            old_value = orig_config_dict.get(key.replace("CONFIG_",""),-1)
            if old_value == -1 :
                # entry did not exist
                line = key + "=" + value
                self.add_line_to_file(orig_file,line)
            else :
                # it already exists, then replace the old value with new value
                if old_value != value :
                    self.replace_line_in_file(orig_file,key,old_value,value)
                else :
                    self.list_of_changes.append("=={} value is unchanged".format(key))

        # add the command line argument - "kmsan.panic=1"
        self.add_argument_to_config_cmdline(orig_file,orig_config_dict,"kmsan.panic=1")

class AddKASAN(BaseConfigConvertor) :

    def __init__(self):
        super().__init__()
        self.default_kasan_dict = {
            "CONFIG_HAVE_ARCH_KASAN"  : "y",
            "CONFIG_HAVE_ARCH_KASAN_VMALLOC" : "y",
            "CONFIG_CC_HAS_KASAN_GENERIC" : "y",
            "CONFIG_KASAN" : "y",
            "CONFIG_KASAN_GENERIC" : "y",
            "CONFIG_KASAN_INLINE" : "y",
            "CONFIG_KASAN_STACK" : "y",
            "CONFIG_KASAN_VMALLOC" : "y"
        }

    def add_KASAN_configurations(self, orig_file) :
        # CHECK FOR THIS !
        orig_config_dict = self.readconfig(orig_file)
        for key,value in self.default_kasan_dict.items() :
            # check if it already exists in the config file
            old_value = orig_config_dict.get(key.replace("CONFIG_",""),-1)
            if old_value == -1 :
                # entry did not exist
                line = key + "=" + value
                self.add_line_to_file(orig_file,line)
            else :
                # it already exists, then replace the old value with new value
                if old_value != value :
                    self.replace_line_in_file(orig_file,key,old_value,value)
                else :
                    self.list_of_changes.append("=={} value is unchanged".format(key))

class VanillaKMSAN(BaseConfigConvertor) :
    """ Not a convertor. Just a verifier for vanilla KMSAN bugs. """

    def check_config_changes(self, config_file) :
        config_dict = self.readconfig(deepcopy(config_file))
        try :
            # check that compiler is CLANG
            assert(config_dict["CC_IS_CLANG"]=="y")
            # check that the below 5 config values are "y"
            # "CONFIG_HAVE_ARCH_KMSAN"  : "y",
            # "CONFIG_HAVE_KMSAN_COMPILER" : "y",
            # "CONFIG_HAVE_KMSAN_PARAM_RETVAL" : "y",
            # "CONFIG_KMSAN" : "y",
            # "CONFIG_KMSAN_CHECK_PARAM_RETVAL" : "y"
            assert(config_dict["HAVE_ARCH_KMSAN"]=="y")
            assert(config_dict["HAVE_KMSAN_COMPILER"]=="y")
            assert(config_dict["HAVE_KMSAN_PARAM_RETVAL"]=="y")
            assert(config_dict["KMSAN"]=="y")
            assert(config_dict["KMSAN_CHECK_PARAM_RETVAL"]=="y")
            # check for argument "kmsan.panic=1"
            assert("kmsan.panic=1" in  config_dict["CMDLINE"])
            return True
        except Exception as e :
            return False

    def verify_with_VanillaKMSAN(self, file_path, src_path) :
        self.verify_with_convertor(file_path, src_path, verifier=self, type="vanilla")

class KASANtoKMSAN(BaseConfigConvertor) :

    def __init__(self):
        super().__init__()
        self.add_kmsan = AddKMSAN()

    def switch_off_KASAN(self,orig_file:List[str]) :
        config_dict = self.readconfig(deepcopy(orig_file))

        # SET CONFIG_KASAN to 'n'
        if config_dict.get("KASAN",-1) == -1 :
            # If CONFIG_KASAN does not exist then add CONFIG_KASAN=n as a safe case
            self.add_line_to_file(orig_file,line="CONFIG_KASAN=n\n")
        else :
            # If CONFIG_KASAN exists then replace the value
            old_val = config_dict["KASAN"]
            new_val = "n"
            if old_val != new_val :
                self.replace_line_in_file(orig_file,"CONFIG_KASAN",old_val,new_val)

        # Remove CONFIG_KASAN_SHADOW_OFFSET
        if config_dict.get("KASAN_SHADOW_OFFSET",-1) != -1 :
            self.remove_line_from_file(orig_file,"CONFIG_KASAN_SHADOW_OFFSET=n")

    def add_KMSAN(self,orig_file:List[str]) :
        self.add_kmsan.add_KMSAN_configurations(orig_file)
        self.list_of_changes += self.add_kmsan.list_of_changes

    def change_config_file(self,orig_file:List[str]) :
        self.reset_list_of_changes()
        self.switch_off_KASAN(orig_file)
        self.add_KMSAN(orig_file)
        complete_config_file = "".join(orig_file)
        return complete_config_file, self.list_of_changes
    
    def change_config_file_for_bug(self, data_path, bug_id:str) :
        changed_flag = False
        config_file = self.get_kernel_config(os.path.join(data_path,bug_id))

        # check if KASAN is even enabled
        config_dict = self.readconfig(deepcopy(config_file))
        if config_dict.get("KASAN",-1) == "n":
            # KASAN is already disabled
            return config_file, changed_flag, []

        config_file_lines = config_file.split("\n")
        config_file_lines = [ele+"\n" for ele in config_file_lines]
        new_config_file, list_of_changes = self.change_config_file(deepcopy(config_file_lines))
        changed_flag = True
        return new_config_file, changed_flag, list_of_changes

    def check_config_changes(self, config_file) :

        config_dict = self.readconfig(deepcopy(config_file))

        try :

            # check that compiler is CLANG
            assert(config_dict["CC_IS_CLANG"]=="y")

            # check that KASAN/KASAN_SHADOW_OFFSET is None or "n"
            assert(config_dict.get("KASAN",None) in ["n", None])
            assert(config_dict.get("KASAN_SHADOW_OFFSET",None) in ["n", None])

            # check that the below 5 config values are "y"
            # "CONFIG_HAVE_ARCH_KMSAN"  : "y",
            # "CONFIG_HAVE_KMSAN_COMPILER" : "y",
            # "CONFIG_HAVE_KMSAN_PARAM_RETVAL" : "y",
            # "CONFIG_KMSAN" : "y",
            # "CONFIG_KMSAN_CHECK_PARAM_RETVAL" : "y"
            assert(config_dict["HAVE_ARCH_KMSAN"]=="y")
            assert(config_dict["HAVE_KMSAN_COMPILER"]=="y")
            assert(config_dict["HAVE_KMSAN_PARAM_RETVAL"]=="y")
            assert(config_dict["KMSAN"]=="y")
            assert(config_dict["KMSAN_CHECK_PARAM_RETVAL"]=="y")
            
            # check for argument "kmsan.panic=1"
            assert("kmsan.panic=1" in  config_dict["CMDLINE"])

            return True

        except Exception as e :
            return False

    def verify_with_KASANtoKMSAN(self, file_path, src_path) :
        self.verify_with_convertor(file_path, src_path, verifier=self, type="KASAN_to_KMSAN")

class KMSANtoKASAN(BaseConfigConvertor) :

    def __init__(self):
        super().__init__()
        self.kmsan_remover = RemoveKMSAN()
        self.add_kasan = AddKASAN()

    def switch_off_KMSAN(self, orig_file:List[str]) :
        self.kmsan_remover.change_config_file(orig_file)
        self.list_of_changes += self.kmsan_remover.list_of_changes

    def add_KASAN(self, orig_file:List[str]) :
        self.add_kasan.add_KASAN_configurations(orig_file)
        self.list_of_changes += self.add_kasan.list_of_changes

    def change_config_file(self,orig_file:List[str]) :
        self.reset_list_of_changes()
        self.switch_off_KMSAN(orig_file)
        self.add_KASAN(orig_file)
        complete_config_file = "".join(orig_file)
        return complete_config_file, self.list_of_changes
    
    def change_config_file_for_bug(self, data_path, bug_id:str) :
        changed_flag = False
        config_file = self.get_kernel_config(os.path.join(data_path,bug_id))

        # check if KMSAN is even enabled
        config_dict = self.readconfig(deepcopy(config_file))
        if config_dict.get("KMSAN",-1) == "n":
            # KMSAN is disabled - cannot continue execution
            return config_file, changed_flag, []

        config_file_lines = config_file.split("\n")
        config_file_lines = [ele+"\n" for ele in config_file_lines]
        new_config_file, list_of_changes = self.change_config_file(deepcopy(config_file_lines))
        changed_flag = True
        return new_config_file, changed_flag, list_of_changes

    def check_config_changes(self, config_file) :

        config_dict = self.readconfig(deepcopy(config_file))

        try :
            # check that KMSAN is disabled
            assert(config_dict.get("KMSAN",None) in ["n", None])
            # check for argument "kmsan.panic=1" - it should not be present
            assert("kmsan.panic=1" not in config_dict["CMDLINE"])

            # check that the below 8 config values are "y"
            assert(config_dict["HAVE_ARCH_KASAN"]=="y")
            assert(config_dict["HAVE_ARCH_KASAN_VMALLOC"]=="y")
            assert(config_dict["CC_HAS_KASAN_GENERIC"]=="y")
            assert(config_dict["KASAN"]=="y")
            assert(config_dict["KASAN_GENERIC"]=="y")
            assert(config_dict["KASAN_INLINE"]=="y")
            assert(config_dict["KASAN_STACK"]=="y")
            assert(config_dict["KASAN_VMALLOC"]=="y")

            return True

        except Exception as e :
            return False

    def KMSANtoKASAN(self, file_path, src_path) :
        self.verify_with_convertor(file_path, src_path, verifier=self, type="KMSAN_to_KASAN")

class SLABtoSLUB(BaseConfigConvertor) :

    def __init__(self) :
        super().__init__()
        self.default_slub_dict = {
            "CONFIG_SLUB" : "y",
            "CONFIG_SLAB_MERGE_DEFAULT" : "y",
            "CONFIG_SLUB_CPU_PARTIAL" : "y",
            "CONFIG_SLUB_DEBUG" : "y"
        }

    def find_SLAB_related_config_values(self,config_dict) :
        """Find all the config values related to SLAB. """
        config_list = []
        for key,value in config_dict.items() :
            if "SLAB" in key.split("_") :
                config_list.append((key,value))
        return config_list
    
    def remove_SLAB_configurations(self, SLAB_keys,orig_file) :
        for info in SLAB_keys :
            key = info[0]
            value = info[1]
            line = "CONFIG_" + key + "=" + value
            self.remove_line_from_file(orig_file,line)
        # explicit config entry that disables SLAB
        self.add_line_to_file(orig_file,"CONFIG_SLAB=n")

    def add_SLUB_configurations(self, orig_file) :
        orig_config_dict = self.readconfig(orig_file)
        for key,value in self.default_slub_dict.items() :
            # check if it already exists in the config file
            old_value = orig_config_dict.get(key.replace("CONFIG_",""),-1)
            if old_value == -1 :
                # entry did not exist
                line = key + "=" + value
                self.add_line_to_file(orig_file,line)
            else :
                # it already exists, then replace the old value with new value
                if old_value != value :
                    self.replace_line_in_file(orig_file,key,old_value,value)
                else :
                    self.list_of_changes.append("=={} value is unchanged".format(key))

    def change_config_file(self,orig_file:List[str]) :
        self.reset_list_of_changes()
        orig_config_dict = self.readconfig(deepcopy(orig_file))
        all_SLAB_keys = self.find_SLAB_related_config_values(orig_config_dict)
        self.remove_SLAB_configurations(all_SLAB_keys,orig_file)
        self.add_SLUB_configurations(orig_file)
        complete_config_file = "".join(orig_file)
        return complete_config_file, self.list_of_changes
    
    def change_config_file_for_bug(self, data_path, bug_id:str) :
        changed_flag = False
        config_file = self.get_kernel_config(os.path.join(data_path,bug_id))

        # check if SLUB is already enabled
        config_dict = self.readconfig(deepcopy(config_file))
        if config_dict.get("SLUB",-1) == "y":
            # SLUB is already enabled
            return config_file, changed_flag, []

        config_file_lines = config_file.split("\n")
        config_file_lines = [ele+"\n" for ele in config_file_lines]
        new_config_file, list_of_changes = self.change_config_file(deepcopy(config_file_lines))
        changed_flag = True
        return new_config_file, changed_flag, list_of_changes

class SLUBtoSLAB(BaseConfigConvertor) :

    def __init__(self) :
        super().__init__()
        self.default_slab_dict = {
            "CONFIG_SLAB" : "y",
            "CONFIG_SLAB_MERGE_DEFAULT" : "y",
            # "CONFIG_DEBUG_SLAB" : "y"
        }
    
    def find_SLUB_related_config_values(self,config_dict) :
        """Find all the config values related to SLUB. """
        config_list = []
        for key,value in config_dict.items() :
            if "SLUB" in key.split("_") :
                config_list.append((key,value))
        return config_list
    
    def remove_SLUB_configurations(self, SLUB_keys,orig_file) :
        for info in SLUB_keys :
            key = info[0]
            value = info[1]
            line = "CONFIG_" + key + "=" + value
            self.remove_line_from_file(orig_file,line)
        # explicit config entry that disables SLUB
        self.add_line_to_file(orig_file,"CONFIG_SLUB=n")

    def add_SLAB_configurations(self, orig_file) :
        orig_config_dict = self.readconfig(orig_file)
        for key,value in self.default_slab_dict.items() :
            # check if it already exists in the config file
            old_value = orig_config_dict.get(key.replace("CONFIG_",""),-1)
            if old_value == -1 :
                # entry did not exist
                line = key + "=" + value
                self.add_line_to_file(orig_file,line)
            else :
                # it already exists, then replace the old value with new value
                if old_value != value :
                    self.replace_line_in_file(orig_file,key,old_value,value)
                else :
                    self.list_of_changes.append("=={} value is unchanged".format(key))

    def change_config_file(self,orig_file:List[str]) :
        self.reset_list_of_changes()
        orig_config_dict = self.readconfig(deepcopy(orig_file))
        all_SLAB_keys = self.find_SLUB_related_config_values(orig_config_dict)
        self.remove_SLUB_configurations(all_SLAB_keys,orig_file)
        self.add_SLAB_configurations(orig_file)
        complete_config_file = "".join(orig_file)
        return complete_config_file, self.list_of_changes
    
    def change_config_file_for_bug(self, data_path, bug_id:str) :
        
        changed_flag = False
        config_file = self.get_kernel_config(os.path.join(data_path,bug_id))

        # check if SLAB is already enabled
        config_dict = self.readconfig(deepcopy(config_file))
        if config_dict.get("SLAB",-1) == "y":
            # SLAB is already enabled
            return config_file, changed_flag, []

        config_file_lines = config_file.split("\n")
        config_file_lines = [ele+"\n" for ele in config_file_lines]
        new_config_file, list_of_changes = self.change_config_file(deepcopy(config_file_lines))
        changed_flag = True
        return new_config_file, changed_flag, list_of_changes

def main() :

    data_path = os.getenv("FIXED_DUMP_PATH")

    kasan_remover = RemoveKASAN()
    new_config_file, changed_flag, list_of_changes = kasan_remover.change_config_file_for_bug(data_path=data_path,bug_id="f5697a2cc8cc739814a87d3755258160e812c9dd")
    print(list_of_changes)
    print()

    kmsan_remover = RemoveKMSAN()
    new_config_file, changed_flag, list_of_changes = kmsan_remover.change_config_file_for_bug(data_path=data_path,bug_id="a2236e7dace23c5338f82242e0d3844ee3ac3e18")
    print(list_of_changes)
    print()

    kasan_to_kmsan = KASANtoKMSAN()
    new_config_file, changed_flag, list_of_changes = kasan_to_kmsan.change_config_file_for_bug(data_path=data_path,bug_id="f5697a2cc8cc739814a87d3755258160e812c9dd")
    print(list_of_changes)
    print()

    slub_to_slab = SLUBtoSLAB()
    new_config_file, changed_flag, list_of_changes = slub_to_slab.change_config_file_for_bug(data_path=data_path,bug_id="cd95cb722bfa1234ac4c78345c8953ee2e7170d0")
    print(list_of_changes)
    print()
    return

if __name__ == '__main__' :
    main()