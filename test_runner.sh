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
docker run --name container-$STAMP$SUFFIX \
           --detach \
           --publish-all \
           image-$STAMP

python tests.py

