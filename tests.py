import json
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


class ContainerIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.base_url = "http://localhost:{}/".format(
            test_container_runner.container_port
        )
        self.tilesets_url = '{}api/v1/tilesets/'.format(self.base_url)
        for i in range(60):  # probably overkill, but Travis is slow sometimes
            try:
                requests.get(self.tilesets_url)
                break
            except Exception:
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
            self.assertRegexpMatches(output.decode('utf-8'), re)

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
        self.tilesets = []
        mock.patch.object(on_startup, "DATA_DIRECTORY", "/tmp/").start()

        with open("test-data/input.json") as f:
            input_dict = json.loads(f.read())
            self.cooler_file_url = input_dict["file_relationships"][0]
            self.bigwig_file_url = input_dict["file_relationships"][3]

        self.cooler_tileset = self._create_tileset(self.cooler_file_url)
        self.bigwig_tileset = self._create_tileset(self.bigwig_file_url)

    def tearDown(self):
        mock.patch.stopall()

    def _create_tileset(self, tileset_url):
        tileset = on_startup.Tileset({"file_url": tileset_url})
        self.tilesets.append(tileset)
        return tileset

    def test_tileset_filetype_is_set(self):
        self.assertEqual(self.cooler_tileset.file_type, "cooler")
        self.assertEqual(self.bigwig_tileset.file_type, "bigwig")

    def test_tileset_datatype_is_set(self):
        self.assertEqual(self.cooler_tileset.data_type, "matrix")
        self.assertEqual(self.bigwig_tileset.data_type, "vector")

    def test_tileset_is_bigwig(self):
        self.assertFalse(self.cooler_tileset.is_bigwig())
        self.assertTrue(self.bigwig_tileset.is_bigwig())

    def _tileset_repr_assertions(self, tileset):
        self.assertEqual(
            "Tileset: {} {} {}".format(
                tileset.file_path,
                tileset.file_type,
                tileset.data_type
            ),
            str(tileset)
        )

    def test_tileset_repr(self):
        for tileset in self.tilesets:
            self._tileset_repr_assertions(tileset)

    def test_tileset_file_downloaded(self):
        for tileset in self.tilesets:
            self.assertTrue(os.path.exists("/tmp/" + tileset.file_name))

    def test_tileset_ingest(self):
        with mock.patch("on_startup.call_command") as call_command_mock:
            self.cooler_tileset.ingest()
            self.bigwig_tileset.ingest()
            self.assertEqual(call_command_mock.call_count, 2)

    @mock.patch("on_startup.call_command")
    @mock.patch("on_startup._fetch_default_viewconf")
    @mock.patch("on_startup._start_nginx")
    def test_module_invocation(self, start_nginx_mock, fetch_default_viewconf_mock, call_command_mock):
        os.environ["INPUT_JSON_URL"] = "http://{}:{}/test-data/input.json".format(
            test_container_runner.test_fixture_server.ip,
            test_container_runner.test_fixture_server.port
        )
        on_startup.main()
        self.assertTrue(fetch_default_viewconf_mock.called)
        self.assertTrue(start_nginx_mock.called)
        self.assertEqual(call_command_mock.call_count, 5)

    @mock.patch('on_startup.error_page')
    def test_error_handling(self, error_page_mock):
        on_startup.main()
        self.assertTrue(error_page_mock.called)

if __name__ == '__main__':
    test_container_runner = TestContainerRunner()
    with test_container_runner:
        unittest.main()
