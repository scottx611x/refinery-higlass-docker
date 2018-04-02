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

PYTHON_SERVER_PORT=9999

get_local_url() {
    local _ip _line
    while IFS=$': \t' read -a _line ;do
        [ -z "${_line%inet}" ] &&
           _ip=${_line[${#_line[1]}>4?1:2]} &&
           [ "${_ip#127.0.0.1}" ] && echo http://$_ip:$PYTHON_SERVER_PORT && return 0
      done< <(LANG=C /sbin/ifconfig)
}

python -m SimpleHTTPServer $PYTHON_SERVER_PORT &
PYTHON_SERVER_PID=$!
docker run --env INPUT_JSON_URL=$(get_local_url)/test-data/input.json \
           --name $CONTAINER_NAME \
           --detach \
           --publish-all \
           --volume /tmp/$CONTAINER_NAME:/refinery-data \
           image-$STAMP

python tests.py

kill $PYTHON_SERVER_PID
rm -r "/tmp/$CONTAINER_NAME"
