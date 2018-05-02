import json
import logging
import mock
import os
import requests
import subprocess
import sys
import time
import unittest

import docker
import on_startup

from test_utils import TestContainerRunner

logger = logging.getLogger(__name__)


class ContainerIntegrationTests(unittest.TestCase):

    def setUp(self):
        client = docker.APIClient(base_url='unix://var/run/docker.sock')
        port = client.port(os.environ["CONTAINER_NAME"], 80)[0]["HostPort"]
        self.base_url = "http://localhost:{}/".format(port)
        self.tilesets_url = '{}api/v1/tilesets/'.format(self.base_url)
        for i in range(60):  # probably overkill, but Travis is slow sometimes
            try:
                requests.get(self.tilesets_url)
                break
            except Exception:
                print('Still waiting for server...', file=sys.stdout)
                time.sleep(1)
        else:
            self.fail('Server never came up')

    def assert_run(self, command, res=[r'']):
        output = subprocess.check_output(
            command.format(**os.environ),
            shell=True
        ).strip()
        for re in res:
            self.assertRegexpMatches(str(output), re)

    def test_home_page(self):
        response = requests.get(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"HiGlass - App", response.content)

    # Test if the data we specify in INPUT_JSON_URL gets ingested properly by
    # higlass server upon container startup
    def test_data_ingested(self):
        response = json.loads(requests.get(self.tilesets_url).content)
        self.assertEqual(response["count"], 5)


class StartupScriptTests(unittest.TestCase):

    def setUp(self):
        mock.patch.object(on_startup, "DATA_DIRECTORY", "/tmp/").start()

        with open("test-data/input.json") as f:
            input_dict = json.loads(f.read())
            self.cooler_file_url = input_dict["file_relationships"][0]
            self.bigwig_file_url = input_dict["file_relationships"][3]

        self.cooler_file_name = self.cooler_file_url.split("/")[-1]
        self.bigwig_file_name = self.bigwig_file_url.split("/")[-1]

        refinery_cooler_node = {"file_url": self.cooler_file_url}
        refinery_bigwig_node = {"file_url": self.bigwig_file_url}

        self.cooler_tileset = on_startup.Tileset(refinery_cooler_node)
        self.bigwig_tileset = on_startup.Tileset(refinery_bigwig_node)

    def tearDown(self):
        mock.patch.stopall()

    def test_tileset_type_meta_info_is_set(self):
        self.assertEqual(self.cooler_tileset.file_type, "cooler")
        self.assertEqual(self.cooler_tileset.data_type, "matrix")

        self.assertEqual(self.bigwig_tileset.file_type, "bigwig")
        self.assertEqual(self.bigwig_tileset.data_type, "vector")

    def test_tileset_is_bigwig(self):
        self.assertFalse(self.cooler_tileset.is_bigwig())
        self.assertTrue(self.bigwig_tileset.is_bigwig())

    def test_tileset_instantiation(self):
        self.assertEqual(self.cooler_tileset.file_url, self.cooler_file_url)
        self.assertEqual(self.cooler_tileset.file_name, self.cooler_file_name)
        self.assertEqual(
            self.cooler_tileset.file_path,
            on_startup.DATA_DIRECTORY + self.cooler_file_name
        )

        self.assertEqual(self.bigwig_tileset.file_url, self.bigwig_file_url)
        self.assertEqual(self.bigwig_tileset.file_name, self.bigwig_file_name)
        self.assertEqual(
            self.bigwig_tileset.file_path,
            on_startup.DATA_DIRECTORY + self.bigwig_file_name
        )

    def test_tileset_repr(self):
        self.assertEqual(
            "Tileset: {} {} {}".format(
                self.cooler_tileset.file_path,
                self.cooler_tileset.file_type,
                self.cooler_tileset.data_type
            ),
            str(self.cooler_tileset)
        )

        self.assertEqual(
            "Tileset: {} {} {}".format(
                self.bigwig_tileset.file_path,
                self.bigwig_tileset.file_type,
                self.bigwig_tileset.data_type
            ),
            str(self.bigwig_tileset)
        )

    def test_tileset_file_downloaded(self):
        self.assertTrue(os.path.exists("/tmp/" + self.cooler_file_name))
        self.assertTrue(os.path.exists("/tmp/" + self.bigwig_file_name))

    def test_tileset_ingest(self):
        with mock.patch("on_startup.call_command") as call_command_mock:
            self.cooler_tileset.ingest()
            self.bigwig_tileset.ingest()
            self.assertEqual(call_command_mock.call_count, 2)

    @mock.patch("django.setup")
    @mock.patch("on_startup.call_command")
    @mock.patch("on_startup._start_nginx")
    def test_module_invocation(
        self, start_nginx_mock, call_command_mock, django_setup_mock
    ):
        os.environ["INPUT_JSON_URL"] = "http://{}:{}/test-data/input.json".format(
            test_container_runner.test_fixture_server.ip,
            test_container_runner.test_fixture_server.port
        )
        with mock.patch.object(on_startup, "__name__", "__main__"):
            on_startup.init()
            self.assertTrue(django_setup_mock.called)
            self.assertTrue(start_nginx_mock.called)
            self.assertEqual(call_command_mock.call_count, 5)

if __name__ == '__main__':
    test_container_runner = TestContainerRunner()
    with test_container_runner:
        suite = unittest.TestLoader().loadTestsFromTestCase(ContainerIntegrationTests)
        suite.addTests(
            unittest.TestLoader().loadTestsFromTestCase(StartupScriptTests)
        )
        result = unittest.TextTestRunner(verbosity=2).run(suite)

    if not result.wasSuccessful():
        sys.exit(1)
