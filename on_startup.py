import os
import requests
import subprocess

import django

from requests.exceptions import RequestException

from django.core.management import call_command

HIGLASS_DATA_TYPE = "higlass_data_type"
HIGLASS_FILE_TYPE = "higlass_file_type"

TILE_SETS = {}


def get_refinery_input_as_json():
    return requests.get(os.environ["INPUT_JSON_URL"]).json()


def populate_higlass_data_directory(data_dir):
    """
    Download remote files specified by urls in the data provided by a GET to
    the provided INPUT_JSON_URL
    :param data_dir: <String> Path to directory to populate with data
    """
    config_data = get_refinery_input_as_json()

    for refinery_node_uuid in config_data["node_info"]:
        TILE_SETS[refinery_node_uuid] = {}

        refinery_node = config_data["node_info"][refinery_node_uuid]
        TILE_SETS[refinery_node_uuid]["file_url"] = refinery_node["file_url"]
        TILE_SETS[refinery_node_uuid]["file_name"] = refinery_node[
            "file_url"].split("/")[-1]

        for key in refinery_node["node_solr_info"].keys():
            if HIGLASS_FILE_TYPE in key.lower():
                TILE_SETS[refinery_node_uuid][HIGLASS_FILE_TYPE] = (
                    refinery_node["node_solr_info"][key]
                )
            if HIGLASS_DATA_TYPE in key.lower():
                TILE_SETS[refinery_node_uuid][HIGLASS_DATA_TYPE] = (
                    refinery_node["node_solr_info"][key]
                )

        try:
            # Streaming GET for potentially large files
            response = requests.get(
                TILE_SETS[refinery_node_uuid]["file_url"],
                stream=True
            )
        except RequestException as e:
            raise RuntimeError(
                "Something went wrong while fetching file from {} : {}".format(
                    TILE_SETS[refinery_node_uuid]["file_url"],
                    e
                )
            )
        else:
            with open(
                '{}{}'.format(
                    data_dir,
                    TILE_SETS[refinery_node_uuid]["file_name"]
                ), 'wb'
            ) as f:
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
    for refinery_node_uuid in TILE_SETS.keys():
        refinery_node_info = TILE_SETS[refinery_node_uuid]
        file_path = data_dir + refinery_node_info["file_name"]

        call_command(
            "ingest_tileset",
            filename=file_path,
            filetype=refinery_node_info[HIGLASS_FILE_TYPE],
            datatype=refinery_node_info[HIGLASS_DATA_TYPE]
        )


if __name__ == '__main__':
    data_dir = "/refinery-data/"
    # Allows for django commands to run in a standalone script
    django.setup()

    populate_higlass_data_directory(data_dir)
    ingest_tilesets(data_dir)

    # Start Nginx only after tilesets have been ingested
    subprocess.run(["/usr/sbin/nginx"])
