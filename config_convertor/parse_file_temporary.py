import os
import json

# job_id, message = try_without_KASAN(data_path=data_folder_path,bug_id=kasan_bug)
# experiment_dict["jobs"].append({"bug_id" : kasan_bug,
#                                 "job_id" : job_id,
#                                 "message" : message,
#                                 "original" : "KASAN",
#                                 "type" : "without_KASAN"})

file_path = os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists/backup_2.txt")
experiment_dict = {"jobs" : []}

with open(file_path,"r") as f :
    lines = f.readlines()
    min_idx = 0
    while(min_idx < len(lines)) :
        sub_lines = lines[min_idx:min_idx+3]

        first_job_info = sub_lines[0]
        first_job_id = first_job_info.split(":")[1].strip()

        bug_info = sub_lines[1]
        bug_id = bug_info.split(":")[0].strip()

        second_job_info = sub_lines[2]
        second_job_id = second_job_info.split(":")[1].strip()
        min_idx += 3

        print("Bug ID {} with KASAN : Job ID {}".format(bug_id,first_job_id))

        first_job_dict = {
            "bug_id" : bug_id,
            "job_id" : first_job_id,
            "message" : "Successful",
            "original" : "KASAN",
            "type" : "vanilla"
        }
        experiment_dict["jobs"].append(first_job_dict)
        
        second_job_dict = {
            "bug_id" : bug_id,
            "job_id" : second_job_id,
            "message" : "Successful",
            "original" : "KASAN",
            "type" : "without_KASAN"
        }
        experiment_dict["jobs"].append(second_job_dict)


        print("Bug ID {} without KASAN : Job ID {}".format(bug_id,second_job_id))

        save_path = os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists")
        final_path = os.path.join(save_path,"trial_1.json")

        with open(final_path,"w") as f :
            json.dump(experiment_dict,f,indent=4)