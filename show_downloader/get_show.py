#!/usr/bin/env python3
"""Download a show given its link"""

import os
import logging
import subprocess

import requests
import urllib.request
import time
from bs4 import BeautifulSoup

import click


logging.basicConfig()


def download_magnet(torrent_file):
    command = ["deluge-console", "add", torrent_file]
    with open(os.devnull, 'wb') as devnull:
        logging.debug(' Adding magnet with command %s', command)
        if subprocess.call(command, stdout=devnull, stderr=devnull):
            return False
    return True


@click.command()
@click.argument('show_url')
def main(show_url):
    response = requests.get(show_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    download_magnet(' '.join(magnet['href'] for magnet in soup.findAll('a', 'sd')))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s : %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    main()
