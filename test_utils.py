import _thread
import datetime
import docker
import os
import shutil
import socket
import sys

from http.server import HTTPServer, SimpleHTTPRequestHandler


class TestFixtureServer(object):

    def __init__(self):
        self.port = 9999
        self.ip = self.get_python_server_ip()

    def get_python_server_ip(self):
        # https://stackoverflow.com/a/166589
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        host_ip = s.getsockname()[0]
        s.close()
        return host_ip

    def _start_server(self):
        server = HTTPServer((self.ip, self.port), SimpleHTTPRequestHandler)
        server.serve_forever()

    def start_server_in_background(self):
        print(
            "Starting Test Fixture Server on: http://{}:{}".format(
                self.ip, self.port
            )
        )
        # start the server in a background thread
        _thread.start_new_thread(self._start_server, ())


class TestContainerRunner(object):
    def __init__(self, repository="scottx611x/refinery-higlass-docker"):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        self.client = docker.from_env()
        self.low_level_client = docker.APIClient(base_url='unix://var/run/docker.sock')

        self.container_name = "container-" + timestamp
        self.container_port = None
        self.image_name = "image-" + timestamp
        self.repository = repository
        self.containers = []

        self.test_fixture_server = TestFixtureServer()
        self.test_fixture_server.start_server_in_background()

        self.outer_volume_path = "/tmp/" + self.container_name
        if not os.path.exists(self.outer_volume_path):
            os.makedirs(self.outer_volume_path)

        self.inner_volume_path = "/refinery-data"

        self._pull_image()
        self._build_image()

    def __enter__(self):
        self.run()

    def __exit__(self, *args):
        if not os.environ.get("CONTINUOUS_INTEGRATION"):
            self.docker_cleanup()

    def _pull_image(self):
        print("Pulling image: {}".format(self.image_name))
        self.client.images.pull(self.repository)

    def _build_image(self):
        print("Building image: {}".format(self.image_name))
        self.client.images.build(
            path=".",
            tag=self.image_name,
            rm=True,
            forcerm=True,
            cache_from=[self.repository]
        )

    def run(self):
        print("Creating container: {}".format(self.container_name))
        container = self.client.containers.run(
            self.image_name,
            detach=True,
            name=self.container_name,
            environment={
                "INPUT_JSON_URL":
                    "http://{}:{}/test-data/input.json".format(
                        self.test_fixture_server.ip,
                        self.test_fixture_server.port
                    )
            },
            ports={"80/tcp": None},
            publish_all_ports=True,
            extra_hosts={socket.gethostname(): self.test_fixture_server.ip},
            volumes={
                self.outer_volume_path: {
                    'bind': self.inner_volume_path, 'mode': 'rw'
                }
            }
        )
        self._set_container_port()
        self.containers.append(container)
        
    def _set_container_port(self):
        self.container_port = self.low_level_client.port(
            self.container_name, 80
        )[0]["HostPort"]

    def docker_cleanup(self):
        print("Cleaning up TestContainerRunner containers/images...")
        for container in self.containers:
            container.remove(force=True, v=True)
        self.client.images.remove(self.image_name)
