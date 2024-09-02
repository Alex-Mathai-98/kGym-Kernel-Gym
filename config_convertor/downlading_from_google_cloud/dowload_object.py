#!/usr/bin/env python

# Copyright 2019 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from google.cloud import storage

class GCBlobDownloader() :

    def __init__(self,api_key,project_id) -> None:
        self.api_key = api_key
        self.project_id = project_id

    def check_if_pattern_exists(self,patterns,blob_name) :
        for patt in patterns :
            if patt in blob_name :
                return patt
        return None

    def download_blob(self,bucket_name, job_id, destination_folder,patterns):
        """Downloads a blob from the bucket."""

        # Output of list buckets
        # <Bucket: kbdr-beta-v0-2-2>
        # <Bucket: kbdr-beta-v0-2-4> 
        # <Bucket: kbdr-beta-v0-2-5> 
        # <Bucket: kbdr-bug-500>
        # <Bucket: kbdr-bug-non-repro>
        # <Bucket: kbdr-dev-0>
        # <Bucket: kbdr-prod-0> 
        # <Bucket: kbdr-runner>
        storage_client = storage.Client(client_options={"api_key": self.api_key, 
                                                        "quota_project_id": self.project_id})
        buckets = list(storage_client.list_buckets())
        # print(buckets)
        
        # Output of list blobs
        # <Blob: kbdr-prod-0, jobs/00000001/0_kbuilder/image.tar.gz, 1710290880134003>, 
        # <Blob: kbdr-prod-0, jobs/00000001/0_kbuilder/kernel, 1710290878578381>, 
        # <Blob: kbdr-prod-0, jobs/00000001/0_kbuilder/kernel.config, 1710290878017352>, 
        # <Blob: kbdr-prod-0, jobs/00000001/0_kbuilder/vmlinux, 1710290894808188>,
        bucket = storage_client.bucket(bucket_name)
        all_blobs = list(bucket.list_blobs(prefix="jobs/{}".format(job_id)))
        # print(all_blobs)
        
        # get the files of interest
        target_data = {}
        for entry in all_blobs :
            patt = self.check_if_pattern_exists(patterns,entry.name)
            if patt is not None:
                key = "_".join(entry.name.split("/")[-2:])
                target_data[key] = entry

        # start downloading the files
        for key,value in target_data.items() :
            if not os.path.exists(os.path.join(destination_folder,job_id)) :
                os.makedirs(os.path.join(destination_folder,job_id))
            destination_file_name = os.path.join(destination_folder,job_id,key)
            value.download_to_filename(destination_file_name)
            print("Downloaded storage object {} from bucket {} to local file {}.".format(
                key, bucket_name, destination_file_name))
