import json
import logging
import mock
import os
import requests
import subprocess
import time
import unittest

import docker
import on_startup

from test_utils import TestContainerRunner

logger = logging.getLogger(__name__)


class CommandlineTest(unittest.TestCase):

    def setUp(self):
        client = docker.APIClient(base_url='unix://var/run/docker.sock')
        port = client.port(os.environ["CONTAINER_NAME"], 80)[0]["HostPort"]
        self.base_url = "http://localhost:{}/".format(port)
        self.tilesets_url = '{}api/v1/tilesets/'.format(self.base_url)
        for i in range(30):
            try:
                requests.get(self.tilesets_url)
                break
            except Exception as e:
                print('Still waiting for server...')
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
            self.big_wig_file_url = input_dict["file_relationships"][3]

        self.test_file_name = self.cooler_file_url.split("/")[-1]

        refinery_cooler_node = {"file_url": self.cooler_file_url}
        refinery_bigwig_node = {"file_url": self.big_wig_file_url}

        self.cooler_tileset = on_startup.Tileset(refinery_cooler_node)
        self.bigwig_tileset = on_startup.Tileset(refinery_bigwig_node)

    def tearDown(self):
        mock.patch.stopall()

        for tileset in [self.cooler_tileset.file_path,
                        self.bigwig_tileset.file_path]:
            if os.path.exists(tileset):
                os.remove(tileset)

    def test_tileset_type_meta_info_is_set_cooler(self):
        self.assertEqual(self.cooler_tileset.file_type, "cooler")
        self.assertEqual(self.cooler_tileset.data_type, "matrix")

    def test_tileset_is_bigwig(self):
        self.assertFalse(self.cooler_tileset.is_bigwig())
        self.assertTrue(self.bigwig_tileset.is_bigwig())

    def test_tileset_type_meta_info_is_set_bigwig(self):
        self.assertEqual(self.bigwig_tileset.file_type, "bigwig")
        self.assertEqual(self.bigwig_tileset.data_type, "vector")

    def test_tileset_instantiation(self):
        self.assertEqual(self.cooler_tileset.file_url, self.cooler_file_url)
        self.assertEqual(self.cooler_tileset.file_name, self.test_file_name)
        self.assertEqual(
            self.cooler_tileset.file_path,
            on_startup.DATA_DIRECTORY + self.test_file_name
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

    def test_tileset_file_downloaded(self):
        self.assertTrue(os.path.exists("/tmp/" + self.test_file_name))

    def test_tileset_ingest(self):
        with mock.patch("on_startup.call_command") as call_command_mock:
            self.cooler_tileset.ingest()
            self.assertTrue(call_command_mock.called)

if __name__ == '__main__':
    test_container_runner = TestContainerRunner()
    with test_container_runner:
        suite = unittest.TestLoader().loadTestsFromTestCase(CommandlineTest)
        suite.addTests(
            unittest.TestLoader().loadTestsFromTestCase(StartupScriptTests)
        )
        result = unittest.TextTestRunner(verbosity=2).run(suite)

    if not result.wasSuccessful():
        sys.exit(1)