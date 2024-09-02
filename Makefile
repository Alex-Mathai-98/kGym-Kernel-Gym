# Useful command line tools for building

# Docker command (add a sudo if no permission)
DOCKER=docker

.PHNOY: kbdr-kscheduler
kbdr-kscheduler: docker/kbdr-kscheduler.Dockerfile
	$(DOCKER) build -f docker/kbdr-kscheduler.Dockerfile -t kbdr-kscheduler:$(TAG) .

.PHNOY: kbdr-kmq
kbdr-kmq: docker/kbdr-kmq.Dockerfile
	$(DOCKER) build -f docker/kbdr-kmq.Dockerfile -t kbdr-kmq:$(TAG) .

.PHNOY: kbdr-dashboard
kbdr-kdashboard: docker/kbdr-kdashboard.Dockerfile
	$(DOCKER) build -f docker/kbdr-kdashboard.Dockerfile -t kbdr-kdashboard:$(TAG) .

.PHNOY: kbdr-kbuilder
kbdr-kbuilder: docker/kbdr-kbuilder.Dockerfile
	$(DOCKER) build -f docker/kbdr-kbuilder.Dockerfile -t kbdr-kbuilder:$(TAG) .

.PHNOY: kbdr-kvmmanager
kbdr-kvmmanager: docker/kbdr-kvmmanager.Dockerfile
	$(DOCKER) build -f docker/kbdr-kvmmanager.Dockerfile -t kbdr-kvmmanager:$(TAG) .

.PHNOY: all-images
all-images: kbdr-kscheduler kbdr-kmq kbdr-kdashboard kbdr-kbuilder kbdr-kvmmanager

.PHNOY: push
push:
	$(DOCKER) tag kbdr-kbuilder:$(TAG) us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kbuilder:$(TAG)
	$(DOCKER) push us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kbuilder:$(TAG)

	$(DOCKER) tag kbdr-kscheduler:$(TAG) us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kscheduler:$(TAG)
	$(DOCKER) push us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kscheduler:$(TAG)

	$(DOCKER) tag kbdr-kvmmanager:$(TAG) us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kvmmanager:$(TAG)
	$(DOCKER) push us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kvmmanager:$(TAG)

	$(DOCKER) tag kbdr-kmq:$(TAG) us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kmq:$(TAG)
	$(DOCKER) push us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kmq:$(TAG)

	$(DOCKER) tag kbdr-kdashboard:$(TAG) us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kdashboard:$(TAG)
	$(DOCKER) push us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kdashboard:$(TAG)

.PHNOY: push-as
push-as:
	$(DOCKER) tag kbdr-kbuilder:$(TAG) us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kbuilder:$(AS)
	$(DOCKER) push us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kbuilder:$(AS)

	$(DOCKER) tag kbdr-kscheduler:$(TAG) us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kscheduler:$(AS)
	$(DOCKER) push us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kscheduler:$(AS)

	$(DOCKER) tag kbdr-kvmmanager:$(TAG) us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kvmmanager:$(AS)
	$(DOCKER) push us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kvmmanager:$(AS)

	$(DOCKER) tag kbdr-kmq:$(TAG) us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kmq:$(AS)
	$(DOCKER) push us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kmq:$(AS)

	$(DOCKER) tag kbdr-kdashboard:$(TAG) us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kdashboard:$(AS)
	$(DOCKER) push us-central1-docker.pkg.dev/llms-for-program-repa-3940/kbdr/kbdr-kdashboard:$(AS)
