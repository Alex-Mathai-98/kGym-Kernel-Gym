# :scroll: Kernel Gym (kGym)

Kernel Gym is a platform that allows for scalable execution of hundreds to thousands of linux kernels within a span of a day. 

:star: With kGym we aim to democratize research at the intersection of machine learning and system software

:star: Using kGym researchers can run LLM experiments on a massive **20 million** lines-of-code codebase like Linux with a few simple API invocations.

## :building_construction: Architecture of kGym

![Architecture](./docs/KernelBench-Detailed-Architecture.png)


## :fire: Architecture Components

 :star: Client Facing Functionalities for Researchers:

- **Clerk** : A simple Python client library for issuing kernel jobs that can compile and execute kernel jobs. For standard users, you need only to get familiar with this library.

:star: Backend functionalities running in the background:

- **Scheduler**: a backend scheduler that schedule jobs across the different virtual machines and also provides information to frontend.
- **Web UI**: a WebUI based on Next.js.
- **RabbitMQ**: message broker.
- **Kbuilder**: containerized worker for building kernels.
- **Kreproducer**: containerized worker for monitoring executions.
- **messager**: a low-level library for communication between  **Kreproducer** and **RabbitMQ**.

## Testing Details

We have tested KGym on a Ubuntu Desktop (with specific details below)

```
~$ uname -a
Linux ********* 6.5.0-35-generic #35~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue May  7 09:00:52 UTC 2 x86_64 x86_64 x86_64 GNU/Linux
```

## Deployment

**kGym currently has a hard requirement of the Google Cloud Platform (GCP)**. 

Note: We understand that being able to run **kGym** on a local server would be the most cost-efficient way for most researchers. And hence we intend to provide this support in the future. 

For the remainder of this tutorial you will need to work with ```gcloud``` - Google's library to interface with GCP.


### Install `gcloud` command line tool

Based on your terminal OS, follow the "Installation instructions" section [here](https://cloud.google.com/sdk/docs/install#installation_instructions).

### Log in and create a new project

After you have installed `gcloud` CLI, login your Google account and create a new project. Type in:

```
demo@kbdr ~ % gcloud init
Welcome! This command will take you through the configuration of gcloud.

Your current configuration has been set to: [default]

You can skip diagnostics next time by using the following flag:
  gcloud init --skip-diagnostics

Network diagnostic detects and fixes local network connection issues.
Checking network connection...done.                                                                                          
Reachability Check passed.
Network diagnostic passed (1/1 checks passed).

You must log in to continue. Would you like to log in (Y/n)?
```

Type in `y`:

```

Your browser has been opened to visit:

    https://accounts.google.com/o/oauth2/auth?xxxxxxxxxxxxxxxx

You are logged in as: [xxxxxxxxx@gmail.com].

Pick cloud project to use: 
 [1] Enter a project ID
 [2] Create a new project
Please enter numeric choice or text value (must exactly match list item):   
```

Type in `2` since we need a new project for KBDr-Runner deployment.

```
Enter a Project ID. Note that a Project ID CANNOT be changed later.
Project IDs must be 6-30 characters (lowercase ASCII, digits, or
hyphens) in length and start with a lowercase letter.
```

Type in the name of the project ID you want. In this example, the project ID is `kbdr-runner-1789`.

```
Waiting for [operations/cp.xxxxxxxxxxxxxxx] to finish...done.                                                            
Your current project has been set to: [kbdr-runner-1789].

Not setting default zone/region (this feature makes it easier to use
[gcloud compute] by setting an appropriate default value for the
--zone and --region flag).
See https://cloud.google.com/compute/docs/gcloud-compute section on how to set
default compute region and zone manually. If you would like [gcloud init] to be
able to do this for you the next time you run it, make sure the
Compute Engine API is enabled for your project on the
https://console.developers.google.com/apis page.

Created a default .boto configuration file at [/Users/xxxxxxxx/.boto]. See this file and
[https://cloud.google.com/storage/docs/gsutil/commands/config] for more
information about configuring Google Cloud Storage.
Your Google Cloud SDK is configured and ready to use!

* Commands that require authentication will use xxxxxxxxx@gmail.com by default
* Commands will reference project `kbdr-runner-1789` by default
Run `gcloud help config` to learn how to change individual settings

This gcloud configuration is called [default]. You can create additional configurations if you work with multiple accounts and/or projects.
Run `gcloud topic configurations` to learn more.
```

Now you have logged in and created a new project for KBDr-Runner.

### Setup billing information

Link your credit card to Google Cloud Platform. More resources can be found [here](https://cloud.google.com/billing/docs/how-to/modify-project).

At this point, we can now request resources and start the deployment.

### Create VMs

In this step, we are going to create computing nodes for the deployment:

- kbdr-main (for kscheduler and kmq)
- kbdr-worker-0 (for kbuilder)
- kbdr-worker-1 (for kvmmanager)

First, let's enable the GCP Compute Engine API:

```
gcloud services enable compute.googleapis.com
```

Once it's enabled, create VMs:

```
gcloud compute instances create kbdr-main \
  --boot-disk-size=100GB \
  --enable-nested-virtualization \
  --machine-type=c2-standard-16 \
  --zone=us-central1-a \
  --image-family=debian-11 \
  --image-project=debian-cloud

gcloud compute instances create kbdr-worker-0 \
  --boot-disk-size=100GB \
  --enable-nested-virtualization \
  --machine-type=c2-standard-30 \
  --zone=us-central1-a \
  --image-family=debian-11 \
  --image-project=debian-cloud

gcloud compute instances create kbdr-worker-1 \
  --boot-disk-size=100GB \
  --enable-nested-virtualization \
  --machine-type=c2-standard-16 \
  --zone=us-central1-a \
  --image-family=debian-11 \
  --image-project=debian-cloud
```

If you encounter the `quota` error, follow the instructions to increase the quota.

### Storage Bucket

First, let's enable the GCP storage API:

```
gcloud services enable storage.googleapis.com
```

Then, create a storage bucket. In this example, we created a bucket named `kbdr-runner-1789`:

```
gcloud storage buckets create gs://kbdr-runner-1789
```

Once it's created, upload Linux distro images to the bucket. Download `userspace-images.zip` from [here](<https://drive.google.com/file/d/15Q8oBaJjMvX81aMUEhrB5LTSP7YtyEDZ/view?usp=sharing>) and place it in the root folder. Then,

```
unzip userspace-images.zip
gcloud storage cp --recursive ./userspace-images gs://kbdr-runner-1789/
```

### Service Accounts

For the purpose of simplicity, in this step, we are going to create one service account with all privileges. **It is not advised to use only one service account for all privileges in production environment**.

```
ACCOUNT_NAME=kbdr-runner-sa
PROJECT_ID=kbdr-runner-1789

gcloud iam service-accounts create $ACCOUNT_NAME \
    --project $PROJECT_ID

SA_EMAIL=$ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com

# Object user permission;
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectUser"

# Compute admin permission;
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/compute.admin"

# Create key;
gcloud iam service-accounts keys create ./assets/sa-credential.json \
    --iam-account="$SA_EMAIL" \
    --key-file-type=json --project $PROJECT_ID

# Place keys for all roles;
cp ./assets/sa-credential.json ./assets/kscheduler-credential.json
cp ./assets/sa-credential.json ./assets/kbuilder-credential.json
cp ./assets/sa-credential.json ./assets/kvmmanager-credential.json
```

### Configure KBDr-Runner Assets

Type in

```
gcloud compute instances list
```

And then you can see the instances we just created and their IP addresses:

```
NAME                      ZONE           MACHINE_TYPE    PREEMPTIBLE  INTERNAL_IP    EXTERNAL_IP  STATUS
kbdr-main                 us-central1-a  c2-standard-16               10.128.0.1                  RUNNING
kbdr-worker-0             us-central1-a  c2-standard-30               10.128.0.2                  RUNNING
kbdr-worker-1             us-central1-a  c2-standard-16               10.128.0.3                  RUNNING
```

We will deploy kscheduler and kmq on kbdr-main. For other workers to connect to kmq, we need a RabbitMQ connection string. Construct such string in this way:

```
amqp://kbdr:ey4lai1the7peeGh@<kbdr-main's internal IP>:5672/?heartbeat=60
```

For the purpose of simplicity, we will use username `kbdr` and passphrase `ey4lai1the7peeGh`.

Once we have the connection string, navigate to `assets` folder and checkout configuration files ended with `.env.template`. For example, copy `kbuilder.env.template` and save it as `kbuilder.env`, then modify `kbuilder.env`:

```
# required: RabbitMQ connection URL, modify the <KMQ Address>;
KBDR_KBUILDER_RABBITMQ_CONN_URL=amqp://kbdr:ey4lai1the7peeGh@<KMQ Address>:5672/?heartbeat=60
# required: Bucket name for storage
GCS_BUCKET_NAME=
```

In this example, the configured `env` file would be:

```
# required: RabbitMQ connection URL, modify the <KMQ Address>;
KBDR_KBUILDER_RABBITMQ_CONN_URL=amqp://kbdr:ey4lai1the7peeGh@10.128.0.1:5672/?heartbeat=60
# required: Bucket name for storage
GCS_BUCKET_NAME=kbdr-runner-1789
```

Configure the following files in such way:

- `kscheduler.env`
- `kvmmanager.env`

### Deploy KBDr-Runner on GCE VMs

Use the deployment scripts to deploy runner nodes. First, cd to KBDr-Runner root folder, upload everything in the KBDr-Runner folder to the remote machines. You can delete the `userspace-images` folder and zip file before upload.

```
gcloud compute scp --recurse ./* kbdr-main:
gcloud compute scp --recurse ./* kbdr-worker-0:
gcloud compute scp --recurse ./* kbdr-worker-1:
```

Then, run the pre-installation scripts on remote machines:

```
gcloud compute ssh kbdr-main --command="./deployment/deploy-new.sh"
gcloud compute ssh kbdr-worker-0 --command="./deployment/deploy-new.sh"
gcloud compute ssh kbdr-worker-1 --command="./deployment/deploy-new.sh"
```

After the pre-installation scripts, build Docker images on each machine and install them as services:

```
gcloud compute ssh kbdr-main --command="echo \"SERVICE_TAG=latest\" > .env && sudo docker compose build kmq kscheduler"
gcloud compute ssh kbdr-worker-0 --command="echo \"SERVICE_TAG=latest\" > .env && sudo docker compose build kbuilder"
gcloud compute ssh kbdr-worker-1 --command="echo \"SERVICE_TAG=latest\" > .env && sudo docker compose build kvmmanager"
```

Start services:

```
gcloud compute ssh kbdr-main --command="sudo docker compose up -d kmq kscheduler"
gcloud compute ssh kbdr-worker-0 --command="sudo docker compose up -d kbuilder"
gcloud compute ssh kbdr-worker-1 --command="sudo docker compose up -d kvmmanager"
```

### Access to `kscheduler` API

Use SSH for port forwarding:

```
gcloud compute ssh kbdr-main \
    -- -NL 8000:localhost:8000
```

`8000` port accesses to the API.
