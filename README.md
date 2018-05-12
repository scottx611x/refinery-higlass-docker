# [refinery-higlass-docker](https://hub.docker.com/r/scottx611x/refinery-higlass-docker/) [![Build Status](https://travis-ci.org/refinery-platform/refinery-higlass-docker.svg?branch=master)](https://travis-ci.org/refinery-platform/refinery-higlass-docker) [![codecov](https://codecov.io/gh/refinery-platform/refinery-higlass-docker/branch/master/graph/badge.svg)](https://codecov.io/gh/refinery-platform/refinery-higlass-docker)
"Refinery-ified" flavor of the higlass-docker (https://github.com/hms-dbmi/higlass-docker/) project

🐳
```docker pull scottx611x/refinery-higlass-docker```

### Pre-Reqs:
- docker
- git
- python 3

### Running tests:
- `pip install -r requirements-test.txt`
- `python tests.py` 
- With coverage: `coverage run tests.py`

```
Ran 9 tests in 47.260s

OK
Cleaning up TestContainerRunner containers...
```

### Releases:
- `git tag -a vX.X.X && git push --tags`
- A new docker image will be built and tagged with the corresponding tag
