# [refinery-higlass-docker](https://hub.docker.com/r/scottx611x/refinery-higlass-docker/) [![Build Status](https://travis-ci.org/refinery-platform/refinery-higlass-docker.svg?branch=master)](https://travis-ci.org/refinery-platform/refinery-higlass-docker)
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
Ran 3 tests in 37.126s

OK
browse:  http://localhost:32921/
shell:   docker exec --interactive --tty container-2018-04-03_10-11-28-standalone bash
logs:    docker exec container-2018-04-03_10-11-28-standalone ./logs.sh
PASS!
```


