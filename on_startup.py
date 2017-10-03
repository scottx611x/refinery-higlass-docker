import glob
import json
import logging
import requests
import subprocess
from requests.exceptions import RequestException

import django
from django.core.management import call_command

logger = logging.getLogger(__name__)


def populate_higlass_data_directory(data_dir):
    """
    Download remote files specified by urls in the input.json file
    :param data_dir: <String> Path to directory to populate with data
    """
    with open("/data/input.json") as f:
        config_data = json.loads(f.read())

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
    files_to_ingest = glob.glob(
        '{}*multires.*'.format(data_dir)
    )

    for filename in files_to_ingest:
        call_command(
            "ingest_tileset",
            filename="{}".format(filename),
            filetype=get_filetype(filename),
            datatype=get_datatype(filename)
        )


def get_datatype(filename):
    datatype_mapping = {
        "cool": "matrix",
        "hitile": "vector"
    }
    try:
        datatype = datatype_mapping[filename.split(".")[-1]]
    except KeyError as e:
        raise RuntimeError(
            "Could not determine datatype from filename: {}".format(
                filename
            )
        )
    else:
        return datatype


def get_filetype(filename):
    filetype_mapping = {
        "cool": "cooler",
        "hitile": "hitile"
    }
    try:
        filetype = filetype_mapping[filename.split(".")[-1]]
    except KeyError:
        raise RuntimeError(
            "Could not determine filetype from filename: {}".format(
                filename
            )
        )
    else:
        return filetype


def swap_app_html():
    subprocess.call(
        [
            "mv",
            "/home/higlass/projects/higlass-website/app/index.html",
            "/home/higlass/projects/higlass-website/index.html"
        ]
    )

if __name__ == '__main__':
    data_dir = "/refinery-data/"

    # Allows for django commands to run in a standalone script
    django.setup()

    populate_higlass_data_directory(data_dir)
    ingest_tilesets(data_dir)

    # Don't switch page until data ingested
    swap_app_html()
