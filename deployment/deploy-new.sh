# Sample machine: $(uname -a) = Linux kbdr-runner-vm 5.10.0-27-cloud-amd64 #1 SMP Debian 5.10.205-2 (2023-12-31) x86_64 GNU/Linux

# From Docker.com;

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl zip unzip -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose -y

# Artifact registry;

cat ./assets/artifact-registry-credential.json | sudo docker login -u _json_key --password-stdin https://us-central1-docker.pkg.dev

# TODO: ramdisk;
