#!/bin/bash

# Argument to develop
if [ "$1" == "--dev" ]; then

  # Check if the container exists
  if [ "$(docker ps -q -f name=point_net_suite)" ]; then
    docker exec -it point_net_suite /bin/bash
    exit
  fi

  docker run -it --name point_net_suite --gpus all --net host --privileged \
    -v data:/data -v $(pwd):/workspace --entrypoint /bin/bash point_net_suite:latest
  exit
fi

docker run -it --name point_net_suite --gpus all --net host --privileged --rm \
  -v data:/data point_net_suite:latest
