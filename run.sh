#!/bin/bash

docker run -it --name point_net_suite --gpus all --net host --privileged --rm \
  -v data:/data point_net_suite:latest
