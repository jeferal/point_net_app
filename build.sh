#! /bin/bash

IMAGE_NAME=point_net_suite
TAG=latest

docker build -t ${IMAGE_NAME}:${TAG} .
