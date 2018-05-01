#!/usr/bin/env bash
set -e

export REPO=scottx611x/refinery-higlass-docker
export STAMP=`date +"%Y-%m-%d_%H-%M-%S"`

export CONTAINER_NAME="container-$STAMP$SUFFIX"

mkdir "/tmp/$CONTAINER_NAME"
coverage run tests.py
rm -r "/tmp/$CONTAINER_NAME"
