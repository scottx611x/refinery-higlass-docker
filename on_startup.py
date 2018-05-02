import os
import requests
import subprocess
import sys

import django
import pyBigWig

from django.core.management import call_command
from requests.exceptions import RequestException

DATA_DIRECTORY = "/refinery-data/"
FILE_URL = "file_url"
FILE_NAME = "file_name"
FILE_PATH = "file_path"
NODE_INFO = "node_info"
NODE_SOLR_INFO = "node_solr_info"


class Tileset(object):
    def __init__(self, refinery_node):
        self.file_type = None
        self.data_type = None
        self.file_url = refinery_node[FILE_URL]
        self.file_name = refinery_node[FILE_URL].split("/")[-1]
        self.file_path = '{}{}'.format(DATA_DIRECTORY, self.file_name)

        self.download()

    def __repr__(self):
        args = [self.file_path, self.file_type, self.data_type]
        return "Tileset: {} {} {}".format(*args)

    def _set_tileset_type_meta(self):
        """
        Set the file_type and data_type information
        for the file underneath self.file_path
        """
        if self.is_bigwig():
            self.file_type = "bigwig"
            self.data_type = "vector"
        else:
            self.file_type = "cooler"
            self.data_type = "matrix"

    def is_bigwig(self):      
        try:
            bw = pyBigWig.open(self.file_path)
        except RuntimeError:  # File isn't a bigwig
            return False
        else:
            is_bigwig = bw.isBigWig()
            bw.close()
            return is_bigwig

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

        self._write_file_to_disk(response)
        response.close()

    def ingest(self):
        """
        Ingest previously downloaded files into higlass-server w/ django
        management command
        """
        try:
            call_command(
                "ingest_tileset",
                filename=self.file_path,
                filetype=self.file_type,
                datatype=self.data_type
            )
        except django.db.utils.IntegrityError as e:
            # TODO: higlass-server code has migration issues.
            # I'm unable to run `makemigrations` which I believe is partly
            # causing the integrity error here.
            # (TileSet.owner is expected to be NOT NULL, although
            # tilesets.models.TileSet.owner has blank=True, null=True)
            # Nevertheless we are still able to create the TileSet objects as
            # necessary
            print(e)

    def _write_file_to_disk(self, response):
        with open(self.file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                # filter out KEEP-ALIVE new chunks
                if chunk:
                    f.write(chunk)
        self._set_tileset_type_meta()


def get_refinery_input():
    """ Make a GET request to acquire the input data for the container"""
    return requests.get(os.environ["INPUT_JSON_URL"]).json()


def _start_nginx():
    # NOTE: The parent process will hang around, but it doesn't hurt anything
    # at this point, and it's probably more hassle than its worth to run
    # NGINX from this script and kill `on_startup.py` without then killing the
    # NGINX process we just started.
    # Its also pretty clear that our intent here is to just `run()`
    # NGINX where any more could be confusing.
    subprocess.run(["/usr/sbin/nginx"])


def main():
    """
    Download remote files specified by urls in the data provided by a GET to
    the provided INPUT_JSON_URL then ingest the downloaded files into Higlass
    Tileset objects
    """
    django.setup()  # Allow django commands to be run (Ex: `ingest_tileset`)

    config_data = get_refinery_input()

    for refinery_node_uuid in config_data[NODE_INFO]:
        refinery_node = config_data[NODE_INFO][refinery_node_uuid]
        Tileset(refinery_node).ingest()

def init():
    if __name__ == '__main__':
        main()
        _start_nginx()  # Start Nginx after all tilesets have been ingested
init()
