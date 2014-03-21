#!/usr/bin/env python
# =============================================================================
# @file   move_episodes.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   12.02.2014
# =============================================================================
"""Move downloaded episodes."""

import os
import re
import shutil
from argparse import ArgumentParser

from fuzzywuzzy import process

_allowed_extensions = ['.mkv', '.mp4', '.avi']

#get_show_list = lambda folder: [os.path.split(os.path.join(folder, element))[1].lower().replace(' ', '.') for element in os.listdir(folder)]
get_show_list = lambda folder: [os.path.split(os.path.join(folder, element))[1] for element in os.listdir(folder)]

def get_episodes(folder):
    """Walk through episodes, also taking into account folders."""
    episode_list = []
    # Escape folder
    for element in os.listdir(folder):
        element = os.path.join(folder, element)
        if os.path.isfile(element):
            # Is file
            if os.path.splitext(element)[1].lower() in _allowed_extensions:
                episode_list.append(element)
        elif os.path.isdir(element):
            # Is folder
            episode_list.extend(get_episodes(element))
        else:
            # What is this?
            raise ValueError("Found weird element in directory")
    return episode_list

def match_episodes(episodes, show_list):
    """Use fuzzywuzzy.

    See:
        http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/
        https://github.com/seatgeek/fuzzywuzzy

    """
    matches = {}
    for episode_path in episodes:
        episode = os.path.split(episode_path)[1]
        matches[episode_path] = process.extractOne(episode, show_list)
    return matches

def find_path_for_episodes(episodes, dest_folder):
    """Find the final path, corresponding to the Season of the show.

    Return {origin: (dest, score)}
    """
    regex = re.compile("[Ss]([0-9][0-9])[Ee][0-9][0-9]")
    alt_regex = re.compile("([0-9])x[0-9][0-9]") # 1x0Y format
    alt_alt_regex = re.compile("([0-9])[0-9][0-9]") # Spanish format
    output = {'move': [], 'keep': []}
    for episode_path, episode_info in episodes.items():
        show, score = episode_info
        match = regex.search(episode_path)
        if not match:
            match = alt_regex.search(episode_path)
            if not match:
                match = alt_alt_regex.search(episode_path)
        if score > 50 and match:
            season = int(match.group(1))
            final_dir = os.path.join(dest_folder, show, 'Season %s' % season)
            final_dest = os.path.join(final_dir, os.path.split(episode_path)[1])
            if not os.path.isdir(final_dir):
                os.mkdir(final_dir)
            output['move'].append((episode_path, final_dest, score))
        else:
            output['keep'].append((episode_path, show, score))
    return output

def send_email(result, dest_folder, extras):
    """Summarize run in a nice email."""
    from email.mime.text import MIMEText
    from subprocess import Popen, PIPE
    # Build message
    if (not result['move']) and (not extras) and (not result['keep']):
        return
    body = "Hola Marta & Albert,\n"
    body += "\n"
    body += "Today I moved the following downloaded files:\n"
    for origin, dest, score in result['move']:
        file_name = os.path.split(origin)[1]
        dest_name = dest.replace(dest_folder, '').replace(file_name, '').lstrip('/')
        body += "  - '%s' to '%s' with score %s\n" % (file_name, dest_name, score)
    if result['keep']:
        body += "\nI didn't move (because I didn't know what to do with them):\n"
        for origin, dest, score in result['keep']:
            file_name = os.path.split(origin)[1]
            body += "  - '%s' to show '%s' with score %s\n" % (file_name, dest, score)
    if extras:
        body += "\nIn addition, I had the follwoing problems:\n%s" % extras
    body += "\n\nSincerely,\nRaspi\n"
    msg = MIMEText(body)
    msg["From"] = "djkarras@gmail.com"
    msg["To"] = "martaetalbert@gmail.com"
    msg["Subject"] = "[Raspi] Shows downloaded"
    p = Popen(["/usr/sbin/sendmail", "-toi"], stdin=PIPE)
    p.communicate(msg.as_string())

def update_xbmc():
    """Update the XBMC video library."""
    from xbmcjson import XBMC
    xbmc = XBMC('http://localhost:8080/jsonrpc')
    # Check everything is OK
    if not xbmc.JSONRPC.Ping()['result'] == 'pong':
        print "Cannot talk to XBMC"
        return
    if not xbmc.VideoLibrary.Scan()['result'] == 'OK':
        print "Failed updating the video library"
    return

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--update-xbmc', action='store_true')
    parser.add_argument('--send-email', action='store_true')
    parser.add_argument('downloads_folder', action='store', type=str)
    parser.add_argument('shows_folder', action='store', type=str)
    args = parser.parse_args()
    # Check folders
    if not os.path.isdir(args.downloads_folder):
        raise ValueError("Downloads folder does not exist!")
    downloads_folder = os.path.abspath(args.downloads_folder)
    if not os.path.isdir(args.shows_folder):
        raise ValueError("Shows folder does not exist!")
    show_folder = os.path.abspath(args.shows_folder)
    # Get show list
    show_list = get_show_list(show_folder)
    # Get episode list
    episodes = get_episodes(downloads_folder)
    # Find which episode goes where (we get a dict)
    episodes_with_show = match_episodes(episodes, show_list)
    # Determine the final path for the episode
    episodes_destination = find_path_for_episodes(episodes_with_show, show_folder)
    extras = ""
    for origin, dest, _ in episodes_destination['move']:
        try:
            os.system('mv "%s" "%s"' % (origin, dest))
            #shutil.copyfile(origin, dest)
            # Cleanup
            #os.remove(origin)
            if not os.path.dirname(origin) == downloads_folder: # Means it was a folder
                shutil.rmtree(os.path.dirname(origin))
        except Exception, e:
            print e
            extras += "Exception moving %s to %s -> %s\n" % (origin, dest, e)
    # Write email
    if args.send_email:
        send_email(episodes_destination, show_folder, extras)
    # Update xbmc
    if args.update_xbmc:
        update_xbmc()

# EOF
