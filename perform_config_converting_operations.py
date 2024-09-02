from perform_sample_build_and_reproduction import KReproducer
import kcomposer.KBDr.kcomposer as kcomp
import os
import json
from typing import Tuple, List
import traceback
import requests
from dotenv import load_dotenv
from config_convertor.downlading_from_google_cloud.dowload_object import GCBlobDownloader
from config_convertor import BaseConfigConvertor, RemoveKASAN, RemoveKMSAN, SLABtoSLUB, SLUBtoSLAB, KASANtoKMSAN, VanillaKMSAN, VanillaKASAN, KMSANtoKASAN

######################### Try different Config Convertors #########################
def get_linker(compiler) :
    if compiler == "gcc" :
        return "ld"
    elif compiler == "clang" :
        return "ld.lld"

def try_with_RemoveKASAN(data_path,bug_id) :
    # Remove KASAN completely from the bug (Bug without any sanitizer)
    try :
        bug_arg_dict = KReproducer.get_empty_reproducer_params()
        bug_arg_dict = KReproducer.fill_kbuilder_kvm_manager_params_from_bug_folder(data_path=data_path,bug_id=bug_id,complete_argument_dict=bug_arg_dict)
        remove_kasan = RemoveKASAN()
        bug_arg_dict["kvm_builder_parameters"]["kernel_config"], changed_config, list_of_changes = remove_kasan.change_config_file_for_bug(data_path=data_path,bug_id=bug_id)
        if not changed_config :
            print("{} : Without KASAN : No need to change the config file".format(bug_id))
            return None, "{} : Without KASAN : No need to change the config file".format(bug_id)
        elif bug_arg_dict["kvm_builder_parameters"]["arch"] != "amd64" :
            # if architecture is not amd64, then just skip for now
            print("{} : Without KASAN : Architecture is not amd64".format(bug_id))
            return None, "{} : Without KASAN : Architecture is not amd64".format(bug_id)
        else :
            print("{} : Without KASAN : Changed the config file".format(bug_id))
            print("List of changes : {}".format("\n".join(list_of_changes)))
            job_id = KReproducer.execute_bug_reproduction(bug_arg_dict)
            return job_id, "Successful"
    except Exception as e :
        job_id = None
        message = "Exception encountered : {}".format(traceback.print_exc())
        return job_id, message

def try_with_RemoveKMSAN(data_path,bug_id) :
    # Remove KMSAN completely from the bug (Bug without any sanitizer)
    try :
        bug_arg_dict = KReproducer.get_empty_reproducer_params()
        bug_arg_dict = KReproducer.fill_kbuilder_kvm_manager_params_from_bug_folder(data_path=data_path,bug_id=bug_id,complete_argument_dict=bug_arg_dict)
        remove_kmsan = RemoveKMSAN()
        bug_arg_dict["kvm_builder_parameters"]["kernel_config"], changed_config, list_of_changes = remove_kmsan.change_config_file_for_bug(data_path=data_path,bug_id=bug_id)
        if not changed_config :
            print("{} : Without KMSAN : No need to change the config file".format(bug_id))
            return None,"{} : Without KMSAN : No need to change the config file".format(bug_id)
        elif bug_arg_dict["kvm_builder_parameters"]["arch"] != "amd64" :
            # if architecture is not amd64, then just skip for now
            print("{} : Without KMSAN : Architecture is not amd64".format(bug_id))
            return None, "{} : Without KMSAN : Architecture is not amd64".format(bug_id)
        else :
            print("{} : Without KMSAN : Changed the config file".format(bug_id))
            print("List of changes : {}".format("\n".join(list_of_changes)))
            job_id = KReproducer.execute_bug_reproduction(bug_arg_dict)
            return job_id, "Successful"
    except Exception as e :
        job_id = None
        message = "Exception encountered : {}".format(traceback.print_exc())
        return job_id, message

def try_with_SLUBtoSLAB(data_path,bug_id) :
    try :
        bug_arg_dict = KReproducer.get_empty_reproducer_params()
        bug_arg_dict = KReproducer.fill_kbuilder_kvm_manager_params_from_bug_folder(data_path=data_path,bug_id=bug_id,complete_argument_dict=bug_arg_dict)
        slub_to_slab = SLUBtoSLAB()
        bug_arg_dict["kvm_builder_parameters"]["kernel_config"], changed_config, list_of_changes = slub_to_slab.change_config_file_for_bug(data_path=data_path,bug_id=bug_id)
        if not changed_config :
            print("{} : SLUB to SLAB : No need to change the config file".format(bug_id))
            return None, "{} : SLUB to SLAB : No need to change the config file".format(bug_id)
        elif bug_arg_dict["kvm_builder_parameters"]["arch"] != "amd64" :
            # if architecture is not amd64, then just skip for now
            print("{} : SLUB to SLAB : Architecture is not amd64".format(bug_id))
            return None, "{} : SLUB to SLAB : Architecture is not amd64".format(bug_id)
        else :
            print("{} : SLUB to SLAB : Changed the config file".format(bug_id))
            print("List of changes : {}".format("\n".join(list_of_changes)))
            job_id = KReproducer.execute_bug_reproduction(bug_arg_dict)
            return job_id, "Successful"
    except Exception as e :
        job_id = None
        message = "Exception encountered : {}".format(traceback.print_exc())
        return job_id, message

def try_with_SLABtoSLUB(data_path,bug_id) :
    try :
        bug_arg_dict = KReproducer.get_empty_reproducer_params()
        bug_arg_dict = KReproducer.fill_kbuilder_kvm_manager_params_from_bug_folder(data_path=data_path,bug_id=bug_id,complete_argument_dict=bug_arg_dict)
        slab_to_slub = SLABtoSLUB()
        bug_arg_dict["kvm_builder_parameters"]["kernel_config"], changed_config, list_of_changes = slab_to_slub.change_config_file_for_bug(data_path=data_path,bug_id=bug_id)
        if not changed_config :
            print("{} : SLAB to SLUB : No need to change the config file".format(bug_id))
            return None, "{} : SLAB to SLUB : No need to change the config file".format(bug_id)
        elif bug_arg_dict["kvm_builder_parameters"]["arch"] != "amd64" :
            # if architecture is not amd64, then just skip for now
            print("{} : SLAB to SLUB : Architecture is not amd64".format(bug_id))
            return None, "{} : SLAB to SLUB : Architecture is not amd64".format(bug_id)
        else :
            print("{} : SLAB to SLUB : Changed the config file".format(bug_id))
            print("List of changes : {}".format("\n".join(list_of_changes)))
            job_id = KReproducer.execute_bug_reproduction(bug_arg_dict)
            return job_id, "Successful"
    except Exception as e :
        job_id = None
        message = "Exception encountered : {}".format(traceback.print_exc())
        return job_id, message

def save_json(data_dict,save_path,final_idx) :
    final_path = os.path.join(save_path,"trial_{}.json".format(final_idx))
    with open(final_path,"w") as f :
        json.dump(data_dict,f,indent=4)

def try_with_KASANtoKMSAN(data_path,bug_id) :
    try :
        bug_arg_dict = KReproducer.get_empty_reproducer_params()
        bug_arg_dict = KReproducer.fill_kbuilder_kvm_manager_params_from_bug_folder(data_path=data_path,bug_id=bug_id,complete_argument_dict=bug_arg_dict)
        kasan_to_kmsan = KASANtoKMSAN()
        bug_arg_dict["kvm_builder_parameters"]["kernel_config"], changed_config, list_of_changes = kasan_to_kmsan.change_config_file_for_bug(data_path=data_path,bug_id=bug_id)
        if not changed_config :
            print("{} : KASAN to KMSAN : No need to change the config file".format(bug_id))
            return None, "{} : KASAN to KMSAN : No need to change the config file".format(bug_id)
        elif bug_arg_dict["kvm_builder_parameters"]["arch"] != "amd64" :
            # if architecture is not amd64, then just skip for now
            print("{} : KASAN to KMSAN : Architecture is not amd64".format(bug_id))
            return None, "{} : KASAN to KMSAN : Architecture is not amd64".format(bug_id)
        else :
            print("{} : KASAN to KMSAN : Changed the config file".format(bug_id))
            print("List of changes : {}".format("\n".join(list_of_changes)))

            bug_arg_dict["kvm_builder_parameters"]["compiler"] = "clang"
            bug_arg_dict["kvm_builder_parameters"]["linker"] = get_linker("clang")
            job_id = KReproducer.execute_bug_reproduction(bug_arg_dict)
            return job_id, "Successful"
    except Exception as e :
        job_id = None
        message = "Exception encountered : {}".format(traceback.print_exc())
        return job_id, message

def try_with_KMSANtoKASAN(data_path,bug_id) :
    try :
        bug_arg_dict = KReproducer.get_empty_reproducer_params()
        bug_arg_dict = KReproducer.fill_kbuilder_kvm_manager_params_from_bug_folder(data_path=data_path,bug_id=bug_id,complete_argument_dict=bug_arg_dict)
        kmsan_to_kasan = KMSANtoKASAN()
        bug_arg_dict["kvm_builder_parameters"]["kernel_config"], changed_config, list_of_changes = kmsan_to_kasan.change_config_file_for_bug(data_path=data_path,bug_id=bug_id)
        if not changed_config :
            print("{} : KMSAN to KASAN : No need to change the config file".format(bug_id))
            return None, "{} : KMSAN to KASAN : No need to change the config file".format(bug_id)
        elif bug_arg_dict["kvm_builder_parameters"]["arch"] != "amd64" :
            # if architecture is not amd64, then just skip for now
            print("{} : KMSAN to KASAN : Architecture is not amd64".format(bug_id))
            return None, "{} : KMSAN to KASAN : Architecture is not amd64".format(bug_id)
        else :
            print("{} : KMSAN to KASAN : Changed the config file".format(bug_id))
            print("List of changes : {}".format("\n".join(list_of_changes)))
            job_id = KReproducer.execute_bug_reproduction(bug_arg_dict)
            return job_id, "Successful"
    except Exception as e :
        job_id = None
        message = "Exception encountered : {}".format(traceback.print_exc())
        return job_id, message

def check_experiment(save_path,data_folder_path) :

    bug_list = os.listdir(data_folder_path)
    bug_list = [bug for bug in bug_list if ".json" in bug]

    KMSAN_bugs = []
    KASAN_bugs = []

    for bug in bug_list :
        with open(os.path.join(data_folder_path,bug),"r") as f :
            bug_data = json.load(f)
        title = bug_data["title"]
        if "KASAN:" in title :
            KASAN_bugs.append(bug)
        elif "KMSAN:" in title :
            KMSAN_bugs.append(bug)
    
    experiment_dict = {"jobs" : []}
    experiment_dict["data_folder_path"] = data_folder_path

    final_idx = -1
    for idx in range(1000) :
        final_path = os.path.join(save_path,"trial_{}.json".format(idx+1))
        if os.path.exists(final_path) :
            continue
        else :
            final_idx = idx+1
            break

    # KASAN related experiments
    # for kasan_bug in KASAN_bugs :
    #     kasan_bug = kasan_bug.replace(".json","")
    #     job_id, message = try_original(data_path=data_folder_path,bug_id=kasan_bug,sanitizer="KASAN")
    #     experiment_dict["jobs"].append({"bug_id" : kasan_bug.replace(".json",""),
    #                                     "job_id" : job_id,
    #                                     "message" : message,
    #                                     "original" : "KASAN",
    #                                     "type" : "vanilla"})
    #     save_json(experiment_dict,save_path,final_idx)
        
    #     job_id, message = try_with_RemoveKASAN(data_path=data_folder_path,bug_id=kasan_bug)
    #     experiment_dict["jobs"].append({"bug_id" : kasan_bug.replace(".json",""),
    #                                     "job_id" : job_id,
    #                                     "message" : message,
    #                                     "original" : "KASAN",
    #                                     "type" : "without_KASAN"})
    #     save_json(experiment_dict,save_path,final_idx)

    #     job_id, message = try_with_SLABtoSLUB(data_path=data_folder_path,bug_id=kasan_bug)
    #     experiment_dict["jobs"].append({"bug_id" : kasan_bug.replace(".json",""),
    #                                     "job_id" : job_id,
    #                                     "message" : message,
    #                                     "original" : "KASAN",
    #                                     "type" : "SLAB_to_SLUB"})
    #     save_json(experiment_dict,save_path,final_idx)

    #     job_id, message = try_with_KASANtoKMSAN(data_path=data_folder_path,bug_id=kasan_bug)
    #     experiment_dict["jobs"].append({"bug_id" : kasan_bug.replace(".json",""),
    #                                     "job_id" : job_id,
    #                                     "message" : message,
    #                                     "original" : "KASAN",
    #                                     "type" : "KASAN_to_KMSAN"})
    #     save_json(experiment_dict,save_path,final_idx)

    # # KMSAN related experiments
    # print("Number of KMSAN bugs : {}".format(len(KMSAN_bugs)))
    # for kmsan_bug in KMSAN_bugs :
    #     kmsan_bug = kmsan_bug.replace(".json","")
    #     job_id, message = try_original(data_path=data_folder_path,bug_id=kmsan_bug,sanitizer="KMSAN")
    #     experiment_dict["jobs"].append({"bug_id" : kmsan_bug.replace(".json",""),
    #                                     "job_id" : job_id,
    #                                     "message" : message,
    #                                     "original" : "KMSAN",
    #                                     "type" : "vanilla"})
    #     save_json(experiment_dict,save_path,final_idx)

    #     job_id, message = try_with_RemoveKMSAN(data_path=data_folder_path,bug_id=kmsan_bug)
    #     experiment_dict["jobs"].append({"bug_id" : kmsan_bug.replace(".json",""),
    #                                     "job_id" : job_id,
    #                                     "message" : message,
    #                                     "original" : "KMSAN",
    #                                     "type" : "without_KMSAN"})
    #     save_json(experiment_dict,save_path,final_idx)

    #     job_id, message = try_with_SLABtoSLUB(data_path=data_folder_path,bug_id=kmsan_bug)
    #     experiment_dict["jobs"].append({"bug_id" : kmsan_bug.replace(".json",""),
    #                                     "job_id" : job_id,
    #                                     "message" : message,
    #                                     "original" : "KMSAN",
    #                                     "type" : "SLAB_to_SLUB"})
    #     save_json(experiment_dict,save_path,final_idx)

    #     job_id, message = try_with_KMSANtoKASAN(data_path=data_folder_path,bug_id=kmsan_bug)
    #     experiment_dict["jobs"].append({"bug_id" : kmsan_bug.replace(".json",""),
    #                                     "job_id" : job_id,
    #                                     "message" : message,
    #                                     "original" : "KMSAN",
    #                                     "type" : "KMSAN_to_KASAN"})
    #     save_json(experiment_dict,save_path,final_idx)
    #     if job_id :
    #         break

    print("Done")

if __name__ == '__main__' :
    # check_experiment(save_path = os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists"),data_folder_path = os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"data"))
    pass