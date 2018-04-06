import json
import mock
import os
import requests
import subprocess
import time
import unittest

from on_startup import DATA_DIRECTORY, Tileset


class CommandlineTest(unittest.TestCase):

    def setUp(self):
        command = "docker port container-{STAMP}{SUFFIX} | " \
            "perl -pne 's/.*://'".format(**os.environ)
        os.environ['PORT'] = subprocess.check_output(
            command, shell=True).strip().decode('utf-8')
        self.base_url = "http://localhost:{PORT}/".format(**os.environ)
        self.tilesets_url = '{}api/v1/tilesets/'.format(self.base_url)

        for i in range(30):
            try:
                requests.get(self.tilesets_url)
                break
            except:
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
            self.assertRegexpMatches(output, re)

    # Tests:
    def test_hello(self):
        self.assert_run('echo "hello?"', [r'hello'])

    def test_home_page(self):
        response = requests.get(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("HiGlass - App", response.content)

    # Test if the data we specify in INPUT_JSON_URL gets ingested properly by
    # higlass server upon container startup
    def test_data_ingested(self):
        response = json.loads(requests.get(self.tilesets_url).content)
        self.assertEqual(response["count"], 4)


class StartupScriptTests(unittest.TestCase):

    def setUp(self):
        self.test_file_name = "test.multires.cool"
        self.file_url = "http://www.example.com/{}".format(self.test_file_name)
        refinery_node = {"file_url": self.file_url}
        self.tileset = Tileset(refinery_node)

    def test_tileset_instantiation(self):
        self.assertEqual(self.tileset.file_url, self.file_url)
        self.assertEqual(self.tileset.file_name, self.test_file_name)
        self.assertEqual(
            self.tileset.file_path,
            DATA_DIRECTORY +
            self.test_file_name)
        self.assertEqual(self.tileset.file_type, "cooler")
        self.assertEqual(self.tileset.data_type, "matrix")

    def test_tileset_download(self):
        with mock.patch("on_startup.Tileset._write_file_to_disk") as write_file_mock:
            self.tileset.download()
            self.assertTrue(write_file_mock.called)

    def test_tileset_ingest(self):
        with mock.patch("on_startup.call_command") as call_command_mock:
            self.tileset.ingest()
            self.assertTrue(call_command_mock.called)

if __name__ == '__main__':
    unittest.main()
