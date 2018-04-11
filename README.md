# [refinery-higlass-docker](https://hub.docker.com/r/scottx611x/refinery-higlass-docker/) [![Build Status](https://travis-ci.org/refinery-platform/refinery-higlass-docker.svg?branch=master)](https://travis-ci.org/refinery-platform/refinery-higlass-docker) [![codecov](https://codecov.io/gh/refinery-platform/refinery-higlass-docker/branch/master/graph/badge.svg)](https://codecov.io/gh/refinery-platform/refinery-higlass-docker)
"Refinery-ified" flavor of the higlass-docker (https://github.com/hms-dbmi/higlass-docker/) project

🐳
```docker pull scottx611x/refinery-higlass-docker```

### Pre-Reqs:
- docker
- git
- python

### Running the Container:
- `pip install -r requirements.txt`
- `./test_runner.sh`

If the tests pass you'll be provided with some info about the currently running container:
```
Ran 6 tests in 25.254s

OK
browse:  http://localhost:32775/
shell:   docker exec --interactive --tty container-2018-04-11_10-09-07-standalone bash
logs:    docker exec container-2018-04-11_10-09-07-standalone ./logs.sh
```


