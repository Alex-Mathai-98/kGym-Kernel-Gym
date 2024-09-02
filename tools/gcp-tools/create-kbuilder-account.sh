echo "Kbuilder GCP service account creation"
echo "Enter the name of the service account to create: "
read ACCOUNT_NAME
echo "Enter the project ID: "
read PROJECT_ID

ACCOUNT_EMAIL=$ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com

gcloud iam service-accounts create $ACCOUNT_NAME \
    --description "For uploading images" \
    --display-name "Builder Worker" \
    --project $PROJECT_ID

# Object user permission;
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$ACCOUNT_EMAIL" \
    --role="roles/storage.objectUser"

# Create key;
gcloud iam service-accounts keys create ./assets/kbuilder-credential.json \
    --iam-account="$ACCOUNT_EMAIL" \
    --key-file-type=json --project $PROJECT_ID
