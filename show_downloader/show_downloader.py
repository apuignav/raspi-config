#!/usr/bin/env python
# =============================================================================
# @file   show_downloader.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   09.02.2014
# =============================================================================
""""""

from datetime import datetime
import os
import string
from lxml import etree
import urllib2, socket

from Containers import TimedDict
import PickleFile

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
        print 'Service Unavailable -> %s' % error
        return []

def download_torrent(torrent_file):
    """Download the torrent in ~/runtime/watch.

    @arg  torrent_file: torrent to download
    @type torrent_file: str
    @arg  dest_file: file name to save
    @type dest_file: str

    @return: boolean upon success/failure

    """

    file_name = os.path.split(torrent_file)[1]
    dest_file = os.path.join(os.environ['HOME'], 'runtime', 'watch', file_name)
    if not os.path.exists(os.path.split(dest_file)[0]):
        print "Folder doesn't exist -> %s" % dest_file
        return False
    if os.path.exists(dest_file):
        print "Destination torrent already exists -> %s" % dest_file
        return False
    try:
        torrent = urllib2.urlopen(torrent_file, timeout=30)
        output = open(dest_file, 'wb')
        output.write(torrent.read())
        output.close()
    except Exception, e:
        print "Problem downloading %s -> %s" % (dest_file, e)
        return False
    return True

def download_shows(feed_list, accept_fail):
    """Download shows from feeds.

    @arg  feeds: list of feeds
    @type feeds: list (or str)
    @arg  accept_fail: accept failed shows as downloaded
    @type accept_fail: bool

    """

    if isinstance(feed_list, str):
        feed_list = [feed_list]
    cache_file = os.path.expanduser('~/runtime/tv_shows.cache')
    cache = TimedDict(3*7*24*3600) # Keys last for a week
    if os.path.exists(cache_file):
        cache = PickleFile.load(cache_file)
    for feed in feed_list:
        feed_info = get_info(feed)
        for episode, episode_date, torrent_file in feed_info:
            #print episode
            if (datetime.today() - episode_date).days > 3*7: # Too old!
                continue
            if episode in cache: # Already downloaded
                continue
            sc = download_torrent(torrent_file)
            if not accept_fail and not sc:
                print "Problems downloading %s" % episode
            else:
                cache.add(episode, episode_date)
    cache.delete_expired()
    PickleFile.write(cache_file, cache)

if __name__ == '__main__':
    import sys
    accept_fail = False
    if len(sys.argv) > 1:
        if '--accept-failures' in sys.argv[1:]:
            accept_fail = True
    download_shows("http://showrss.info/user/15673.rss?magnets=false&namespaces=true&name=null&quality=null&re=null",
                   accept_fail)

# EOF
