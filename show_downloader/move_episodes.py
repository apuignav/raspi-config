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

from delugectl import cleanup_torrents, start_deluge, is_deluge_running

# Deluge stuff

_allowed_extensions = ['.mkv', '.mp4', '.avi']
re_tv = re.compile(r'(.+?)'
                   r'[ .][Ss](\d\d?)[Ee](\d\d?)|(\d\d?)x(\d\d?)|(\d\d?)(\d\d)'
                   r'.*?'
                   r'(?:[ .](\d{3}\d?p)|\Z)?')

re_season = re.compile(r"[Ss](\d\d?)[Ee](\d\d?)|(\d\d?)x(\d\d?)|(\d)(\d\d)")

# Reasons for failing
_reasons = {'season': "I couldn't determine season number",
            'score': "I couldn't determine show name due to low score"}

get_show_list = lambda folder: [os.path.split(os.path.join(folder, element))[1]
                                for element in os.listdir(folder)]

def get_episodes(folder):
    """Walk through episodes, also taking into account folders."""
    episode_list = []
    # Escape folder
    for element in os.listdir(folder):
        element = os.path.join(folder, element)
        if os.path.isfile(element):
            # Is file
            if os.path.splitext(element)[1].lower() in _allowed_extensions:
                if not 'sample' in element.lower():
                    episode_list.append(element)
        elif os.path.isdir(element):
            # Is folder
            episode_list.extend(get_episodes(element))
        else:
            # What is this?
            raise ValueError("Found weird element in directory")
    return episode_list

def analyze_episode(file_name):
    """Anayze episode to find name, season and episode number."""
    tv_data = re_tv.match(file_name)
    if tv_data:
        return tv_data.group(1).replace(".", " "), tv_data.group(2), tv_data.group(3)
    return None

def match_episodes(episodes, show_list):
    """Use fuzzywuzzy only if needed.

    See:
        http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/
        https://github.com/seatgeek/fuzzywuzzy

    """
    episode_matching = {'matched': [],
                        'notmatched': []}
    for episode_path in episodes:
        episode = os.path.split(episode_path)[1]
        episode_info = analyze_episode(episode)
        show_name = None
        if episode_info:
            show_name, season, _ = episode_info
        else:
            match = re_season.search(episode)
            if not match:
                episode_matching['notmatched'].append((episode_path, 'season'))
                continue
            season = next((val for val in match.groups()[::2] if val), None)
            show_name = episode
        season = int(season)
        if not show_name in show_list:
            extract_res = process.extractOne(show_name.replace('.', ' ').replace('_', ' '),
                                             show_list, score_cutoff=85)
            if not extract_res:
                episode_matching['notmatched'].append((episode_path, 'score'))
                continue
            show_name, _ = extract_res
        episode_matching['matched'].append((episode_path, show_name, season))
    return episode_matching['matched'], episode_matching['notmatched']

def find_path_for_episodes(episodes, dest_folder):
    """Find the final path, corresponding to the Season of the show.

    Return [(origin, dest)]
    """
    output = []
    for episode_path, show_name, season in episodes:
        final_dir = os.path.join(dest_folder, show_name, 'Season %s' % season)
        final_dest = os.path.join(final_dir, os.path.split(episode_path)[1])
        if not os.path.isdir(final_dir):
            os.mkdir(final_dir)
        output.append((episode_path, final_dest))
    return output

def format_body(dest_folder, episodes_moved, episodes_not_moved, extra_problems):
    body = "Today I moved the following downloaded files:\n"
    for origin, dest in episodes_moved:
        file_name = os.path.split(origin)[1]
        dest_name = dest.replace(dest_folder, '').replace(file_name, '').lstrip('/')
        body += "  - '%s' to '%s'\n" % (file_name, dest_name)
    if episodes_not_moved:
        body += "\nI didn't move:\n"
        for file_name, reason in episodes_not_moved:
            file_name = os.path.split(file_name)[1]
            body += "  - '%s' because %s\n" % (file_name,
                                               _reasons.get(reason, 'of an unknown reason'))
    if extra_problems:
        body += "\nIn addition, I had the follwoing problems:\n%s" % '\n'.join(extra_problems)
    return body

def send_push(body):
    from pibullet.device import Device
    myself = Device(os.path.expanduser('~/.pibullet'))
    myself.notify('Raspi digest', body)

def send_email(body):
    """Summarize run in a nice email."""
    from email.mime.text import MIMEText
    from subprocess import Popen, PIPE
    text = "Hola Marta & Albert,\n"
    body += "\n"
    text += body
    text += "\n\nSincerely,\nRaspi\n"
    msg = MIMEText(text)
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
    try:
        #if not xbmc.JSONRPC.Ping()['result'] == 'pong':
            #print "Cannot talk to XBMC"
            #return
        if not xbmc.VideoLibrary.Scan()['result'] == 'OK':
            print "Failed updating the video library"
    except Exception, e:
        print "Failed updating the video library -> %s" % e
    return

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--update-xbmc', action='store_true')
    parser.add_argument('--send-email', action='store_true')
    parser.add_argument('--send-push', action='store_true')
    parser.add_argument('downloads_folder', action='store', type=str)
    parser.add_argument('shows_folder', action='store', type=str)
    args = parser.parse_args()
    # Get deluge situation, stop and clean
    was_deluge_running = is_deluge_running()
    cleanup_torrents(raise_on_fail=False)
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
    episodes_with_show, episodes_unmatched = match_episodes(episodes, show_list)
    # Determine the final path for the episodes that were matched
    episodes_destination = find_path_for_episodes(episodes_with_show, show_folder)
    # Protect folders with non-matched episodes
    folders_to_protect = set([os.path.dirname(file_name)
                              for file_name, _ in episodes_unmatched] +
                             [downloads_folder])
    # Move
    problems = []
    folders_to_remove = []
    for origin, dest in episodes_destination:
        try:
            os.system('mv "%s" "%s"' % (origin, dest))
            #print 'mv "%s" "%s"' % (origin, dest)
            #shutil.copyfile(origin, dest)
            # Cleanup
            origin_folder = os.path.dirname(origin)
            if not origin_folder in folders_to_protect:
                folders_to_remove.append(origin_folder)
        except Exception, exception:
            print exception
            problems.append("Exception moving %s to %s -> %s\n" % (origin, dest, exception))
    # Now remove
    for folder_to_remove in set(folders_to_remove):
        #print "Remove", folder_to_remove
        shutil.rmtree(folder_to_remove)
    # Put deluge in previous status
    if was_deluge_running:
        start_deluge()
    # Format body
    body = format_body(show_folder, episodes_destination, episodes_unmatched, problems)
    # Communicate if I did something
    if episodes_with_show or episodes_unmatched:
        # Write email
        if args.send_email:
            send_email(body)
            send_push(body)
        else:
            print body
        # Update xbmc
        if args.update_xbmc:
            update_xbmc()

# EOF
