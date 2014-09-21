#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# @file   cleanup_deluge.py
# @author Albert Puig (albert.puig@cern.ch)
# @date   21.09.2014
# =============================================================================
"""Cleanup deluge of finished torrents."""

import os

from PickleFile import load, write

config_folder = '/home/pi/.config/deluge/'

def stop_deluge():
    """Stop deluge."""
    os.system('sudo stop deluge')

def cleanup(delete_fastresume=True):
    """Cleanup deluge before moving torrent files.

    1) Load the torrents.state file
    2) Get finished torrents.
    3) Remove them.
    4) Save modified torrents.state.

    :param bool delete_fastresume: Delete torrents.fastresume file?

    :returns: Number of deleted torrents.
    :rtype: int

    :raises: OSError: if no .torrent file is found for a finished torrent

    """
    stop_deluge()
    state_folder = os.path.join(config_folder, 'state')
    state_file = os.path.join(state_folder, 'torrents.state')
    state = load(state_file)
    finished_torrents = [torrent for torrent in state.torrents if torrent.is_finished]
    num_finished_torrents = len(finished_torrents)
    if num_finished_torrents != 0:
        for torrent in finished_torrents:
            torrent_file = os.path.join(state_folder, '%s.torrent' % torrent.torrent_id)
            if not os.path.exists:
                raise OSError("Cannot find torrent file -> %s" % torrent_file)
            os.remove(torrent_file)
        state.torrents = [torrent for torrent in state.torrents if not torrent.is_finished]
        write(state_file, state)
        if delete_fastresume:
            fastresume_file = os.path.join(state_folder, 'torrents.fastresume')
            if os.path.exists(fastresume_file):
                os.remove(fastresume_file)
    return num_finished_torrents

if __name__ == '__main__':
    cleaned_files = cleanup()
    print "I cleaned %s files" % cleaned_files


# EOF
