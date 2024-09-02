gcloud compute instances create $1 \
    --boot-disk-size=100GB \
    --enable-nested-virtualization \
    --machine-type=c2-standard-30 \
    --network=https://www.googleapis.com/compute/v1/projects/llms-for-program-repa-3940/global/networks/default \
    --zone=us-central1-a \
    --no-address \
    --image-family=debian-11 \
    --image-project=debian-cloud