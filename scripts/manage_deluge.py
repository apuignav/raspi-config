#!/usr/bin/env python
# =============================================================================
# @file   manage_deluge.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   09.02.2014
# =============================================================================
""""""

from deluge.log import setupLogger
setupLogger()

from deluge.ui.client import client
from twisted.internet import reactor
from deluge.log import setupLogger
setupLogger()

def pause():
    def pause_all_torrents():
        return client.core.pause_all_torrents()
    print "Telling Deluge to pause all torrents."
    tell_deluge_to(pause_all_torrents)

def resume():
    def resume_all_torrents():
        return client.core.resume_all_torrents()
    print "Telling Deluge to resume all torrents."
    tell_deluge_to(resume_all_torrents)


def tell_deluge_to(act):
    def on_connect_success(result):
        def disconnect(result):
            client.disconnect()
            reactor.crash()
        act().addCallback(disconnect)

    def on_connect_fail(result):
        print "Connection failed!"

    d = client.connect()
    d.addCallback(on_connect_success)
    d.addErrback(on_connect_fail)
    reactor.run()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    # Create the subparser for the pause command
    parser_pause = subparsers.add_parser('pause')
    parser_pause.set_defaults(func=pause)
    # Create the subparser for the pause command
    parser_resume = subparsers.add_parser('resume')
    parser_resume.set_defaults(func=resume)
    # Execute!
    args = parser.parse_args()
    args.func()

# EOF