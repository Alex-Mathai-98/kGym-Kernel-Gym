from perform_sample_build_and_reproduction import JobAnalyzer, KReproducer
from perform_config_converting_operations import try_with_RemoveKASAN, try_with_RemoveKMSAN
import json

def collect_aborted_jobs(all_job_path,from_dict:dict=None) :
    """ Collect all the aborted jobs """
    if from_dict is None :
        with open(all_job_path,"r") as f :
            all_job_dict = json.load(f)
    else :
        all_job_dict = from_dict
    ans = []
    for job_ele in all_job_dict["jobs"] :
        job_id = job_ele["job_id"]
        if job_id is None :
            # this job was not executed in the first place
            continue
        job_info = JobAnalyzer.get_important_job_info(job_id)
        if job_info["status"] == "aborted" :
            ans.append(job_ele)
    return ans

def retry_aborted_jobs(all_job_path) :
    """ Collect all aborted jobs from the 'all_job_path' and retry them. """

    with open(all_job_path,"r") as f :
        all_job_dict = json.load(f)

    # create backup of "all_job_path"
    with open(all_job_path.replace(".json","") + "_backup.json","w") as f :
        json.dump(all_job_dict,f,indent=4)

    data_folder_path = all_job_dict["data_folder_path"]
    aborted_jobs = collect_aborted_jobs(all_job_path=None,from_dict=all_job_dict)

    if len(aborted_jobs) == 0 :
        print("No aborted jobs")
        return

    for aborted_job in aborted_jobs :
        if aborted_job["type"] == "vanilla":
            # try vanilla again
            job_id, message = KReproducer.try_original(data_path=data_folder_path,bug_id=aborted_job["bug_id"])
        elif aborted_job["type"] == "without_KASAN":
            # try without KASAN
            job_id, message = try_with_RemoveKASAN(data_path=data_folder_path,bug_id=aborted_job["bug_id"])
        elif aborted_job["type"] == "without_KMSAN" :
            # try without KMSAN
            job_id, message = try_with_RemoveKMSAN(data_path=data_folder_path,bug_id=aborted_job["bug_id"])
        # update information about job_id and message
        aborted_job["job_id"] = job_id
        aborted_job["message"] = message

    with open(all_job_path,"w") as f :
        json.dump(all_job_dict,f,indent=4)

def aggregate_job_results(all_job_path, job_type:str='simple_reproduction') :

    if job_type == "cross_reproduction" :
        
        with open(all_job_path,"r") as f :
            all_job_data = json.load(f)
        
        crash_counter = 0
        all_set_up_failed = 0
        all_lost_connection = 0
        all_no_output = 0
        all_no_crash = 0
        lost_connection_and_no_output = 0
        total_run = 0

        job_list = all_job_data["jobs"]
        for job in job_list :
            instance_set_up_failed = False
            lost_connection_flag = False
            no_output_from_machine = False
            no_crash_flag = False
            crash_flag = False
            
            if job.get("execution", None) :
                if job["execution"].get("results", None) :
                    results = job["execution"]["results"]
                    total_run += 1
                    for res in results :
                        if res["crash_description"] is None and res["message"] == "Failed to set up instance":
                            instance_set_up_failed = True
                        if res["crash_description"] is None and res["message"] == "No crash reproduced":
                            no_crash_flag = True
                        elif res["crash_description"] is None :
                            pass
                        elif res["crash_description"] == "lost connection to test machine" :
                            lost_connection_flag = True
                        elif res["crash_description"] == "no output from test machine" :
                            no_output_from_machine = True
                        else :
                            crash_flag = True
                            crash_counter += 1
                            print("Bug ID : {}, Description : {}".format(job["bug_id"],res["crash_description"]))
                            break
                    
                    if not crash_flag and \
                        not lost_connection_flag and \
                        not no_output_from_machine and \
                        no_crash_flag :
                        all_no_crash += 1
        
                    elif not crash_flag and \
                        not lost_connection_flag and \
                        not no_output_from_machine and \
                        instance_set_up_failed :
                        all_set_up_failed += 1

                    elif not crash_flag and \
                        lost_connection_flag and \
                        not no_output_from_machine and \
                        not instance_set_up_failed :
                        all_lost_connection += 1

                    elif not crash_flag and \
                        not lost_connection_flag and \
                        no_output_from_machine and \
                        not instance_set_up_failed :
                        all_no_output += 1
        
                    elif not crash_flag and \
                        (lost_connection_flag or no_output_from_machine) and \
                        not instance_set_up_failed :
                        lost_connection_and_no_output += 1

        print("Total run : {}".format(total_run))

        print("Crash Counter : {}".format(crash_counter))
        print("All set up failed : {}".format(all_set_up_failed))
        print("All no output : {}".format(all_no_output))
        print("All no crash reproduced : {}".format(all_no_crash))
        print("Lost connection and No output : {}".format(lost_connection_and_no_output))
        print("Total stats : {}".format(crash_counter+all_set_up_failed+all_no_output+all_no_crash))

    elif job_type == "simple_reproduction" :

        with open(all_job_path,"r") as f :
            all_job_data = json.load(f)
        
        crash_counter = 0
        all_set_up_failed = 0
        all_lost_connection = 0
        all_no_output = 0
        all_no_crash = 0
        lost_connection_and_no_output = 0
        total_run = 0
        aborted_jobs = 0

        job_list = all_job_data["jobs"]
        for job in job_list :
            instance_set_up_failed = False
            lost_connection_flag = False
            no_output_from_machine = False
            no_crash_flag = False
            crash_flag = False
            
            if job.get("execution", None) :
                results = [job["execution"]]
                total_run += 1

                if job["execution"]["status"] == "aborted" :
                    aborted_jobs += 1
                    continue

                for res in results :
                    if res["crash_description"] is None and res["message"] == "Failed to set up instance":
                        instance_set_up_failed = True
                    if res["crash_description"] is None and res["message"] == "No crash reproduced":
                        no_crash_flag = True
                    elif res["crash_description"] is None :
                        pass
                    elif res["crash_description"] == "lost connection to test machine" :
                        lost_connection_flag = True
                    elif res["crash_description"] == "no output from test machine" :
                        no_output_from_machine = True
                    else :
                        crash_flag = True
                        crash_counter += 1
                        print("Bug ID : {}, Description : {}".format(job["bug_id"],res["crash_description"]))
                        break
                
                if not crash_flag and \
                    not lost_connection_flag and \
                    not no_output_from_machine and \
                    no_crash_flag :
                    all_no_crash += 1
    
                elif not crash_flag and \
                    not lost_connection_flag and \
                    not no_output_from_machine and \
                    instance_set_up_failed :
                    all_set_up_failed += 1

                elif not crash_flag and \
                    lost_connection_flag and \
                    not no_output_from_machine and \
                    not instance_set_up_failed :
                    all_lost_connection += 1

                elif not crash_flag and \
                    not lost_connection_flag and \
                    no_output_from_machine and \
                    not instance_set_up_failed :
                    all_no_output += 1
    
                elif not crash_flag and \
                    (lost_connection_flag or no_output_from_machine) and \
                    not instance_set_up_failed :
                    lost_connection_and_no_output += 1

        print("Total run : {}".format(total_run))
        print("Aborted Jobs : {}".format(aborted_jobs))
        print("Crash Counter : {}".format(crash_counter))
        print("All set up failed : {}".format(all_set_up_failed))
        print("All no output : {}".format(all_no_output))
        print("All no crash reproduced : {}".format(all_no_crash))
        print("Lost connection and No output : {}".format(lost_connection_and_no_output))
        print("Total stats : {}".format(aborted_jobs+crash_counter+all_set_up_failed+all_no_output+all_no_crash+lost_connection_and_no_output))

def print_final_changes(list_of_json_paths,
                        save_path) :
    """ Print final variations of each bug. """
    
    final_dict = {}

    for json_path in list_of_json_paths :
        
        with open(json_path,"r") as f :
            json_dict = json.load(f)
        jobs_list = json_dict["jobs"]

        for job in jobs_list :
            bug_id = job["bug_id"].replace(".json","")
            execution_type = job["type"]
            
            if final_dict.get(bug_id,-1) == -1 :
                final_dict[bug_id] = {}
            
            if job["job_id"] :
                # the job was actually run
                if job["execution"]["status"] == "aborted" :
                    final_dict[bug_id][execution_type] = {}
                    final_dict[bug_id][execution_type]["executed"] = False
                    final_dict[bug_id][execution_type]["output"] = "aborted"
                else :
                    final_dict[bug_id][execution_type] = {}
                    final_dict[bug_id][execution_type]["executed"] = True
                    if job["execution"]["message"] :    
                        final_dict[bug_id][execution_type]["output"] = job["execution"]["message"]
                    elif job["execution"]["crash_description"] :
                        final_dict[bug_id][execution_type]["output"] = job["execution"]["crash_description"]
                final_dict[bug_id][execution_type]["job_id"] = job["job_id"]

            else :
                # the job did not run
                final_dict[bug_id][execution_type] = {}
                final_dict[bug_id][execution_type]["executed"] = False
                final_dict[bug_id][execution_type]["job_id"] = None
                final_dict[bug_id][execution_type]["output"] = job["message"]

    with open(save_path,"w") as f :
        json.dump(final_dict,f,indent=4)

if __name__ == '__main__' :
    # print_final_changes(list_of_json_paths=[os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists/trial_1.json"),
    #                                         os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists/trial_2.json"),
    #                                         os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists/trial_3.json"),
    #                                         os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists/trial_4.json"),
    #                                         os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists/trial_5.json"),
    #                                         os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists/trial_6.json")],
    #                     save_path = os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists/final_summary.json")
    
    # kasan_to_kmsan = KASANtoKMSAN()
    # kasan_to_kmsan.verify_with_KASANtoKMSAN(file_path=os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists/trial_5.json"),
    #                         src_path=os.path.join(os.getenv("KGYM_PATH"),"config_convertor/trial_folder"))

    # kmsan_to_kasan = KMSANtoKASAN()
    # kmsan_to_kasan.KMSANtoKASAN(file_path=os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH",/sublists/trial_8.json",
    #                         src_path=os.path.join(os.getenv("KGYM_PATH"),"config_convertor/trial_folder"))
    pass