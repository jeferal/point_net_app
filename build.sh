#! /bin/bash

IMAGE_NAME=point_net_app
TAG=latest

docker build -t ${IMAGE_NAME}:${TAG} .
