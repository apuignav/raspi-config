#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
# @file   find_repacked_duplicates.py
# @author Albert Puig (albert.puig@cern.ch)
# @date   05.03.2016
# =============================================================================
"""Check for duplicate shows that have been repacked."""

import os

REPACKED_WORDS = ['REPACKED', 'PROPER']

for base_dir, folders, files in os.walk(os.path.expandvars('$HOME/Series')):
    # Check we are in a show folder
    if not files:
        pass
    if len(files) == 1 and files[0] == '.DS_Store':
        pass
    # Locate duplicates
    for file_name in files:
	if file_name.endswith('.srt'):
            continue
        for word in REPACKED_WORDS:
            if word in file_name:
                for file_ in files:
                    if file_.endswith('.srt'):
                        continue
                    if file_.startswith(file_name.split(word)[0]) and \
                            file_ is not file_name:
			print "Do you want to replace?"
			print file_
			print "with"
			print file_name
			answer = raw_input("[y/n]")
			if answer.lower() == 'y':
			    os.remove(os.path.join(base_dir, file_))

# EOF

