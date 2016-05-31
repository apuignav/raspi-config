#!/usr/bin/env python
# =============================================================================
# @file   show_downloader.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   05.03.2016
# =============================================================================
"""Add magnet links to Deluge."""

from datetime import datetime
import os
import string
import subprocess
import urllib2
import socket
import argparse
import logging

from lxml import etree

from Containers import TimedDict
import PickleFile

PROPER_WORDS = ["PROPER", "REPACK"]


def get_info(feed):
    """Get title, published date and torrent of shows from feed.

    @arg  feed: feed address
    @type feed: string

    @return: list of tuples (title, date, torrent file)

    """
    try:
        req = urllib2.Request(feed, headers={'User-Agent': "Magic Browser"}) # Hack to avoid 403 HTTP
        url = urllib2.urlopen(req, timeout=30)
        tree = etree.parse(url)
        titles = tree.xpath("/rss/channel/item/title[not (contains(., '720p') or contains(., '720P'))]/text()")
        published_dates = tree.xpath("/rss/channel/item/pubDate/text()")
        torrent_files = tree.xpath("/rss/channel/item/link[not (contains(., '720p') or contains(., '720P'))]/text()")
        return [(filter(lambda x: x in string.printable, titles[i]),
                 datetime.strptime(published_dates[i], '%a, %d %b %Y %H:%M:%S +0000'),
                 str(torrent_files[i])) for i in range(len(titles))]
    except (etree.XMLSyntaxError, urllib2.URLError, socket.timeout), error:
        logging.critical('Service Unavailable -> %s', error)
        return []


def sanitize_feed(feed_list):
    """Remove duplicate episodes due to REPACK and PROPER.

    @arg  feed_list: episodes found
    @type feed_list: list of tuples, output of get_info

    @return: list of tuples (title, date, torrent file)

    """
    # Find shows that have been uploaded twice
    repacked_episodes = []
    for show_title, _, _ in feed_list:
        for proper_word in PROPER_WORDS:
            if proper_word in show_title:
                repacked_episodes.append(show_title.replace(proper_word, '').strip())
    final_list = []
    for show_title, date, magnet in feed_list:
        if show_title not in repacked_episodes:
            final_list.append((show_title, date, magnet))
    return final_list


def download_torrent(torrent_file):
    """Get the torrent.

    If it's a magnet link, add it to deluge, otherwise
    download it to ~/runtime/watch.

    @arg  torrent_file: torrent to download
    @type torrent_file: str
    @arg  dest_file: file name to save
    @type dest_file: str

    @return: boolean upon success/failure

    """
    if torrent_file.startswith("magnet:"):  # Magnet!!
        command = ["deluge-console", "add", torrent_file]
        with open(os.devnull, 'wb') as devnull:
            #if subprocess.call(command, stdout=devnull, stderr=devnull):
            logging.debug(' Adding magnet with command %s', command)
            if subprocess.call(command, stderr=devnull):
                return False
    else:
        file_name = os.path.split(torrent_file)[1]
        dest_file = os.path.join(os.environ['HOME'], 'runtime', 'watch', file_name)
        if not os.path.exists(os.path.split(dest_file)[0]):
            logging.error("Folder doesn't exist -> %s", dest_file)
            return False
        if os.path.exists(dest_file):
            logging.warning("Destination torrent already exists -> %s", dest_file)
            return False
        try:
            torrent = urllib2.urlopen(torrent_file, timeout=30)
            output = open(dest_file, 'wb')
            output.write(torrent.read())
            output.close()
        except Exception, e:
            logging.error("Problem downloading %s -> %s", dest_file, e)
            return False
    return True


def download_shows(feed_list, accept_fail, download):
    """Download shows from feeds.

    @arg  feeds: list of feeds
    @type feeds: list (or str)
    @arg  accept_fail: accept failed shows as downloaded
    @type accept_fail: bool
    @arg  download: download?
    @type download: bool

    """

    if isinstance(feed_list, str):
        feed_list = [feed_list]
    cache_file = os.path.expanduser('~/runtime/tv_shows.cache')
    cache = TimedDict(3*7*24*3600) # Keys last for a week
    if os.path.exists(cache_file):
        cache = PickleFile.load(cache_file)
    for feed in feed_list:
        feed_info = sanitize_feed(get_info(feed))
        # print 'Today is', datetime.today()
        # print 'Initial cache'
        # for key in cache:
        #    print ' -', key
        for episode, episode_date, torrent_file in feed_info:
            logging.debug('Found episode: %s %s', episode, torrent_file)
            if (datetime.today() - episode_date).days > 3*7: # Too old!
                logging.debug(' Too old')
                continue
            if episode in cache: # Already downloaded
                logging.debug(' Already downloaded')
                continue
            # print 'Downloading?', download
            if download:
                logging.debug( ' Downloading!')
                sc = download_torrent(torrent_file)
            else:
                sc = True
            if not accept_fail and not sc:
                logging.error("Problems downloading %s", episode)
            else:
                cache.add(episode, episode_date)
    # print 'Cache before deleting expired'
    # for key in cache:
    #    print ' -', key
    cache.delete_expired()
    # print 'Final cache'
    # for key in cache:
    #    print ' -', key
    PickleFile.write(cache_file, cache)


if __name__ == '__main__':
    # Parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--accept-failures', action='store_true')
    parser.add_argument('--no-download', action='store_true')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    # Logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s : %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    download_shows("http://showrss.info/user/15673.rss?magnets=true&namespaces=true&name=clean&quality=null&re=null",
                   args.accept_failures,
                   not args.no_download)

# EOF
