echo "Enter the bucket name: "
read BUCKET_NAME

gcloud storage buckets create gs://$BUCKET_NAME
