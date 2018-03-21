import glob
import json
import logging
import os
import requests
import subprocess
from requests.exceptions import RequestException

import django
from django.core.management import call_command

logger = logging.getLogger(__name__)

FILE_TYPE = "filetype"
DATA_TYPE = "datatype"

big_wig_mappings = {
    FILE_TYPE: "bigwig",
    DATA_TYPE: "vector"
}
FILENAME_MAPPINGS = {
    "beddb": {
        FILE_TYPE: "beddb",
        DATA_TYPE: "bedlike"
    },
    "bigwig": big_wig_mappings,
    "bw": big_wig_mappings,
    "cool": {
        FILE_TYPE: "cooler",
        DATA_TYPE: "matrix"
    },
    "db": {
        FILE_TYPE: "arrowhead-domains",
        DATA_TYPE: "bed2ddb"
    },
    "hibed": {
        FILE_TYPE: "hibed",
        DATA_TYPE: "stacked-interval"
    },
    "multires": {
        FILE_TYPE: "multivec",
        DATA_TYPE: "multi-vector"
    }
}


def populate_higlass_data_directory(data_dir):
    """
    Download remote files specified by urls in the data provided by a GET to the provided INPUT_JSON_URL
    :param data_dir: <String> Path to directory to populate with data
    """
    config_data = requests.get(os.environ["INPUT_JSON_URL"]).json()

    for url in config_data["file_relationships"]:
        try:
            # Streaming GET for potentially large files
            response = requests.get(url, stream=True)
        except RequestException as e:
            raise RuntimeError(
                "Something went wrong while fetching file from {} : {}".format(
                    url,
                    e
                )
            )
        else:
            with open('{}{}'.format(data_dir, url.split("/")[-1]), 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    # filter out KEEP-ALIVE new chunks
                    if chunk:
                        f.write(chunk)
        finally:
            response.close()


def ingest_tilesets(data_dir):
    """
   Ingest previously downloaded files into higlass-server w/ django
   management command
   :param data_dir: <String> Path to directory populated with data to ingest
   """
    files_to_ingest = glob.glob('{}*.*'.format(data_dir))

    for filename in files_to_ingest:
        try:
            filename_mappings = FILENAME_MAPPINGS[
                filename.split(".")[-1].lower()]
        except KeyError:
            raise RuntimeError(
                "Could not determine filename_mappings from filename: {}".format(
                    filename
                )
            )
        call_command(
            "ingest_tileset",
            filename="{}".format(filename),
            filetype=filename_mappings[FILE_TYPE],
            datatype=filename_mappings[DATA_TYPE]
        )

if __name__ == '__main__':
    data_dir = "/refinery-data/"

    # Allows for django commands to run in a standalone script
    django.setup()

    populate_higlass_data_directory(data_dir)
    ingest_tilesets(data_dir)

    # Start Nginx only after tilesets have been ingested
    subprocess.run(["/usr/sbin/nginx"])
