#!/usr/bin/env python
# @file   utils.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   17.03.2013

from fabric.api import settings, run

def dir_exists(dir_name):
    with settings(warn_only=True):
        return not run('test -d {0}'.format(dir_name)).failed

def file_exists(file_name):
    with settings(warn_only=True):
        return not run('test -f {0}'.format(file_name)).failed

def to_boolean(arg):
    ret = bool(arg)
    if isinstance(arg, str):
        if arg.lower() == 'false' or arg == '0':
            ret = False
    return ret

# EOF

