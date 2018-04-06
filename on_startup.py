import os
import requests
import subprocess

import django

from requests.exceptions import RequestException

from django.core.management import call_command

DATA_DIRECTORY = "/refinery-data/"
FILE_URL = "file_url"
FILE_NAME = "file_name"
FILE_PATH = "file_path"
NODE_INFO = "node_info"
NODE_SOLR_INFO = "node_solr_info"


class Tileset(object):

    def __init__(self, refinery_node):
        self.file_url = refinery_node[FILE_URL]
        self.file_name = refinery_node[FILE_URL].split("/")[-1]
        self.file_path = '{}{}'.format(DATA_DIRECTORY, self.file_name)
        self.file_type = "cooler"
        self.data_type = "matrix"

    def download(self):
        """
        Download a tileset from a `file_url` to disk at a `file_path`
        """
        try:
            # Streaming GET for potentially large files
            response = requests.get(self.file_url, stream=True)
        except RequestException as e:
            raise RuntimeError(
                "Something went wrong while fetching file from {} : {}".format(
                    self.file_url,
                    e
                )
            )

        with open(self.file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                # filter out KEEP-ALIVE new chunks
                if chunk:
                    f.write(chunk)

        response.close()

    def ingest(self):
        """
        Ingest previously downloaded files into higlass-server w/ django
        management command
        :param tileset_dict: dict containing information about a tileset
        """
        call_command(
            "ingest_tileset",
            filename=self.file_path,
            filetype=self.file_type,
            datatype=self.data_type
        )


def get_refinery_input():
    """ Make a GET request to acquire the input data for the container"""
    return requests.get(os.environ["INPUT_JSON_URL"]).json()


def main():
    """
    Download remote files specified by urls in the data provided by a GET to
    the provided INPUT_JSON_URL then ingest the downloaded files into Higlass
    Tileset objects
    """
    config_data = get_refinery_input()

    for refinery_node_uuid in config_data[NODE_INFO]:
        refinery_node = config_data[NODE_INFO][refinery_node_uuid]
        tileset = Tileset(refinery_node)
        tileset.download()
        tileset.ingest()


if __name__ == '__main__':
    # Allows for django commands to run in a standalone script
    django.setup()

    main()

    # Start Nginx only after all tilesets have been ingested.
    # NOTE: The parent process will hang around, but it doesn't hurt anything
    # at this point, and it's probably more hassle than its worth to run
    # NGINX from this script and kill `on_startup.py` without then killing the
    # NGINX process we just started.
    # Its also pretty clear that our intent here is to just `run()`
    # NGINX where any more could be confusing.
    subprocess.run(["/usr/sbin/nginx"])
