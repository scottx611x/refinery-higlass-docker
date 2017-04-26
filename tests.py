import json
import os
import requests
import subprocess
import time
import unittest


class CommandlineTest(unittest.TestCase):
    def setUp(self):
        command = "docker port container-{STAMP}{SUFFIX} | perl -pne 's/.*://'".format(**os.environ)
        os.environ['PORT'] = subprocess.check_output(command, shell=True).strip().decode('utf-8')
        self.url = 'http://localhost:{PORT}/api/v1/tilesets/'.format(
            **os.environ)
        while True:
            if 0 == subprocess.call('curl --fail --silent '+self.url+' > /dev/null', shell=True):
                break
            print('still waiting for server...')
            time.sleep(1)

    def assertRun(self, command, res=[r'']):
        output = subprocess.check_output(command.format(**os.environ), shell=True).strip()
        for re in res:
            self.assertRegexpMatches(output, re)

    # Tests:
    def test_hello(self):
        self.assertRun('echo "hello?"', [r'hello'])

    # Test if the data we specify in input.json gets ingested properly by
    # higlass server upon container startup
    def test_data_ingested(self):
        response = json.loads(requests.get(self.url).content)
        self.assertEqual(
            response["results"][0]["name"],
            "dixon2012-h1hesc-hindiii-allreps-filtered.1000kb.multires.cool"
        )


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
    if result.wasSuccessful():
        print('PASS!')
    else:
        print('FAIL!')
        exit(1)
