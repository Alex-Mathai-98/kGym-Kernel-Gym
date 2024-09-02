gcloud compute ssh $1 --command="sudo rm -rf ~/*"
gcloud compute scp --recurse assets/ $1:
gcloud compute scp --recurse deployment/ $1:
gcloud compute scp *.yml $1:
