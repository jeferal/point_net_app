#!/bin/bash

# Argument to develop
if [ "$1" == "--dev" ]; then
  docker run -it --name point_net_suite --gpus all --net host --privileged --rm \
    -v data:/data -v $(pwd):/workspace --entrypoint /bin/bash point_net_suite:latest
  exit
fi

docker run -it --name point_net_suite --gpus all --net host --privileged --rm \
  -v data:/data point_net_suite:latest
