#!/bin/bash

docker run --name point_net_app --gpus all --net host --privileged --rm \
  -v data:/data point_net_app:latest
