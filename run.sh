#!/bin/bash

docker run --name point_net_suite --gpus all --net host --privileged --rm point_net_suite:latest \
  -v data:/data \
