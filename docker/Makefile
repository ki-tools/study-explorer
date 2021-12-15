CONTAINER_NAME=study-explorer
IMAGE_NAME=$(CONTAINER_NAME)

# Build the docker image.
.PHONY: build
build:
	sudo docker build --tag $(IMAGE_NAME) --tag $(CONTAINER_NAME) .


# Run the image in the background from the local image.
.PHONY: run_local
run_local:
	docker-compose up -d -f docker-compose-local.yml


# Run the image in the background from the published image.
.PHONY: run
run:
	docker-compose up -d


# List volumes.
.PHONY: list_volumes
list_volumes:
	sudo docker volume ls


# List all images.
.PHONY: list_images
list_images:
	sudo docker images -a


# Delete the image from Docker.
.PHONY: rm_image
rm_image:
	sudo docker image rm $(IMAGE_NAME)


# List all running containers.
.PHONY: ps
ps:
	sudo docker ps -a


# Start a stopped container.
.PHONY: start
start:
	sudo docker start $(CONTAINER_NAME)


# Stop a running container.
.PHONY: stop
stop:
	sudo docker stop $(CONTAINER_NAME)


# Delete the container from Docker.
.PHONY: rm_container
rm_container:
	sudo docker rm $(CONTAINER_NAME)


# Pull the image from Synapse.
.PHONY: pull
pull:
	sudo docker pull $(IMAGE_NAME)


# Build and publish the container to Synapse.
.PHONY: push
push: build
	sudo docker login
	sudo docker push $(IMAGE_NAME)
