import _thread
import docker
import os
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
            ), file=sys.stdout
        )
        # start the server in a background thread
        _thread.start_new_thread(self._start_server, ())


class TestContainerRunner(object):

    def __init__(self):
        self.client = docker.from_env()
        self.container_name = os.environ["CONTAINER_NAME"]
        self.image_name = "image-" + os.environ["STAMP"]
        self.repository = os.environ["REPO"]
        self.containers = []

        self.test_fixture_server = TestFixtureServer()
        self.test_fixture_server.start_server_in_background()

        self.outer_volume_path = "/tmp/" + self.container_name
        self.inner_volume_path = "/refinery-data"

        self._pull_image()
        self._build_image()

    def __enter__(self):
        self.run()

    def __exit__(self, *args):
        if not os.environ.get("CONTINUOUS_INTEGRATION"):
            self.docker_cleanup()

    def _pull_image(self):
        print("Pulling image: {}".format(self.image_name), file=sys.stdout)
        self.client.images.pull(self.repository)

    def _build_image(self):
        print("Building image: {}".format(self.image_name), file=sys.stdout)
        self.client.images.build(
            path=".",
            tag=self.image_name,
            rm=True,
            forcerm=True,
            cache_from=[self.repository]
        )

    def run(self):
        print("Creating container: {}".format(self.container_name), 
              file=sys.stdout)
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
        self.containers.append(container)

    def docker_cleanup(self):
        print("Cleaning up TestContainerRunner containers/images...", 
              file=sys.stdout)
        for container in self.containers:
            container.remove(force=True, v=True)
        self.client.images.remove(self.image_name)
