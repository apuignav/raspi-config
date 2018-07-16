#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# @file   delugectl.py
# @author Albert Puig (albert.puig@cern.ch)
# @date   21.09.2014
# =============================================================================
"""Manage deluge."""

import os

from RunCommand import run_command
from PickleFile import load, write

config_folder = os.path.expandvars('$HOME/.config/deluge/')


def is_deluge_running():
    """Is deluge running?"""
    return 'running' in run_command('sudo', 'systemctl', 'status', 'deluged')[2]

def start_deluge():
    """Start deluge."""
    run_command('sudo', 'systemctl', 'start', 'deluged', 'deluge-web')

def stop_deluge():
    """Stop deluge."""
    run_command('sudo', 'systemctl', 'stop', 'deluged', 'deluge-web')

def cleanup_torrents(delete_fastresume=True, raise_on_fail=True, restart=False):
    """Cleanup deluge before moving torrent files.

    1) Load the torrents.state file
    2) Get finished torrents.
    3) Remove them.
    4) Save modified torrents.state.

    :param bool delete_fastresume: Delete torrents.fastresume file?
    :param bool raise_on_fail: Raise exception if torrent file is not found.

    :returns: Number of deleted torrents.
    :rtype: int

    :raises: OSError: if no .torrent file is found for a finished torrent

    """
    stop_deluge()
    state_folder = os.path.join(config_folder, 'state')
    state_file = os.path.join(state_folder, 'torrents.state')
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        state = load(state_file)
    # for torrent in state.torrents:
    #     print torrent, torrent.is_finished
    finished_torrents = [torrent for torrent in state.torrents if torrent.is_finished]
    num_finished_torrents = len(finished_torrents)
    if num_finished_torrents != 0:
        for torrent in finished_torrents:
            torrent_file = os.path.join(state_folder, '%s.torrent' % torrent.torrent_id)
            if not os.path.exists(torrent_file):
                if raise_on_fail:
                    raise OSError("Cannot find torrent file -> %s" % torrent_file)
            else:
                os.remove(torrent_file)
        state.torrents = [torrent for torrent in state.torrents if not torrent.is_finished]
        write(state_file, state)
        if delete_fastresume:
            fastresume_file = os.path.join(state_folder, 'torrents.fastresume')
            if os.path.exists(fastresume_file):
                os.remove(fastresume_file)
    if restart:
        start_deluge()
    return num_finished_torrents

if __name__ == '__main__':
    cleaned_files = cleanup_torrents()
    print "I cleaned %s files" % cleaned_files


# EOF
