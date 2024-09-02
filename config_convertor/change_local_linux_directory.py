import os
import json
import subprocess
from pydriller import Git

def save_to_dot_config(kernel_config, linux_path) :
    with open(os.path.join(linux_path,".config"), "w") as f :
        f.write(kernel_config)

    with open(os.path.join(linux_path,".config_for_comparison"), "w") as f :
        f.write(kernel_config)

def perform_git_clean(linux_path) :
    old_path = os.getcwd()
    os.chdir(linux_path)
    result = subprocess.run(["git clean -f -d"], shell=True, capture_output=True, text=True)
    os.chdir(old_path)

    old_path = os.getcwd()
    os.chdir(linux_path)
    result = subprocess.run(["git clean -f -d"], shell=True, capture_output=True, text=True)
    os.chdir(old_path)

def prepare_for_data_point(linux_path,data_path) :
    
    # load bug data
    if os.path.exists(os.path.join(data_path,"original_data.json")) :
        with open(os.path.join(data_path,"original_data.json"),"r") as f :
            bug_data = json.load(f)
    else :
        with open(data_path+".json","r") as f :
            bug_data = json.load(f)

    # perform git checkout
    kernel_source_commit = bug_data["crashes"][0]["kernel-source-commit"]
    perform_git_clean(linux_path)
    git_repo = Git(linux_path)
    git_repo.checkout(kernel_source_commit)
    
    # get kernel config
    kernel_config_data = bug_data["crashes"][0]["kernel-config-data"]
    save_to_dot_config(kernel_config_data,linux_path)


def main() :
    # Important note - KMSAN needs the clang compiler (it does not work with GCC)
    # seed_path = os.path.join(os.getenv("KGYM_PATH"),"seeds_folder")
    # grep -r "\"title\": \"KMSAN:" seed_path
    # grep -r "\"title\": \"KMSAN:"  os.getenv("FIXED_DUMP_PATH")

    # grep -r "\"title\": \"KASAN:" seed_path
    # grep -r "\"title\": \"KASAN:" os.getenv("FIXED_DUMP_PATH")
    
    bug_id = "7572ea29c46caf35dfdbf55f48bd129d89aec05a"
    prepare_for_data_point(linux_path=os.getenv("LINUX_PATH"),data_path=os.path.join(os.getenv("FIXED_DUMP_PATH"),"{}".format(bug_id)))

    return

if __name__ == '__main__' :
    main()