#!/usr/bin/env python
# @file   utils.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   17.03.2013

from fabric.api import settings, run

def dirExists(dirName):
    with settings(warn_only=True):
        return not run('test -d {0}'.format(dirName)).failed

# EOF

