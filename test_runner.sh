#!/usr/bin/env bash
set -e

REPO=scottx611x/refinery-higlass-docker
export STAMP=`date +"%Y-%m-%d_%H-%M-%S"`

docker pull $REPO # Defaults to "latest", but just speeds up the build, so precise version doesn't matter.
docker build --cache-from $REPO \
             --tag image-$STAMP \
             .

# Keep this simple: We want folks just to be able to run the bare Docker container.
# If this starts to get sufficiently complicated that we want to put it in a script
# by itself, then it has gotten too complicated.
export SUFFIX=-standalone
echo "image-$STAMP"

CONTAINER_NAME="container-$STAMP$SUFFIX"

mkdir "/tmp/$CONTAINER_NAME"

docker run --name $CONTAINER_NAME \
           --detach \
           --publish-all \
           --volume /tmp/$CONTAINER_NAME:/refinery-data \
           image-$STAMP

python tests.py

rm -r "/tmp/$CONTAINER_NAME"
