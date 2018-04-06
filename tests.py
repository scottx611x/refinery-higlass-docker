import json
import os
import requests
import subprocess
import sys
import time
import unittest

PYTHON_TEST_SERVER_PID = sys.argv[1]


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


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(CommandlineTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    lines = [
        'browse:  http://localhost:{PORT}/',
        'shell:   docker exec --interactive --tty container-{STAMP}{SUFFIX} bash',
        'logs:    docker exec container-{STAMP}{SUFFIX} ./logs.sh'
    ]
    for line in lines:
        print(line.format(**os.environ))

    # Kill PYTHON_TEST_SERVER
    subprocess.call(["kill", PYTHON_TEST_SERVER_PID])

    if result.wasSuccessful():
        print('PASS!')
    else:
        print('FAIL!')
        exit(1)
