import glob
import json
import requests

import django
from django.core.management import call_command


django.setup()


def populate_higlass_data_directory(data_dir):
    with open("/data/input.json") as f:
        config_data = json.loads(f.read())

    for url in config_data["file_relationships"]:
        response = requests.get(url)
        with open('{}{}'.format(data_dir, url.split("/")[-1]), 'wb') as f:
            f.write(response.content)


def ingest_tilesets(settings, data_directory):
    cooler_files_to_ingest = glob.glob(
        '{}*multires.cool'.format(data_directory)
    )

    for filename in cooler_files_to_ingest:
        call_command(
            "ingest_tileset",
            filename="{}".format(filename),
            filetype="cooler",
            datatype="matrix"

        )

if __name__ == '__main__':
    higlass_data_dir = "/home/higlass/projects/higlass-server"
    settings_file = "{}/higlass-server/settings.py".format(higlass_data_dir)
    data_dir = "/tmp/"

    populate_higlass_data_directory(data_dir)
    ingest_tilesets(higlass_data_dir, data_dir)
