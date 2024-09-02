from config_convertor.downlading_from_google_cloud.dowload_object import GCBlobDownloader
import os
import json
from typing import Tuple, List


######################### Job Downloader #########################
class JobDownloader() :

    @classmethod
    def download_results(cls, job_id_list, dst_folder, patterns) :
        # GCBlobDownloader
        gc_downloader = GCBlobDownloader(api_key=os.getenv("GOOGLE_CLOUD_API_KEY"),project_id=os.getenv("PROJECT_ID"))

        for job_id in job_id_list :
            gc_downloader.download_blob(bucket_name="kbdr-prod-0",
                                        job_id=job_id,
                                        destination_folder=dst_folder,
                                        patterns=patterns)

    @classmethod
    def download_results_from_file(cls,
                                file_path,
                                dst_folder,
                                patterns=["kernel.config","report"]) :

        with open(file_path,"r") as f :
            job_data = json.load(f)

        job_list = []
        for job in job_data["jobs"] :
            if job["job_id"] :
                job_list.append(job["job_id"].replace("\"",""))

        cls.download_results(job_list,dst_folder,patterns)
################################################################

if __name__ == '__main__' :
    # download_results_from_file(file_path=os.path.join(base_path,"easy_experiment_data/sublists/final_benchmark_with_parent_commit.json"),
    #                         dst_folder=os.path.join(base_path,"easy_experiment_data/google_cloud_data"),
    #                         patterns=["kernel.config", "report","log0","syz-crush.log"])
    pass