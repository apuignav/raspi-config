#!/usr/bin/env python
# =============================================================================
# @file   backup.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   28.01.2014
# =============================================================================
"""XBMC backup utils."""

import os
import shutil
import argparse

def do_backup(args):
    """Backup /home/pi/.xbmc dir to backup.tar.gz.

    The tar file will go to the folder specified in args.folder.

    """
    output_file = os.path.join(args.folder, 'backup.tar.gz')
    if os.path.exists(output_file):
        os.remove(output_file)
    os.system("sudo stop xbmc")
    os.system("cd /home/pi && tar -cvzf %s .xbmc" % output_file)
    os.system("sudo start xbmc")
    print "Backed up to %s" % output_file

def restore_backup(args):
    """Restore backup to  /home/pi/.xbmc.

    The tar file to restore is given by args.backup_folder.

    """
    if not os.path.exists(args.backup_file):
        print "Cannot find backup file %s" % args.backup_file
        return
    shutil.copy(args.backup_file, '/home/pi/')
    os.system("sudo stop xbmc")
    os.system("cd /home/pi && tar -xzf backup.tar.gz && rm backup.tar.gz")
    os.system("sudo start xbmc")
    print "Restored backup from %s" % args.backup_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    # Parser for the backup command
    backup_parser = subparsers.add_parser("backup")
    backup_parser.add_argument('folder', action='store', type=str, help="Folder to copy the backup file to")
    backup_parser.set_defaults(func=do_backup)
    # Parser for the restore command
    restore_parser = subparsers.add_parser("restore")
    restore_parser.add_argument('backup_file', action='store', type=str, help="Backup file to restore from")
    restore_parser.set_defaults(func=restore_backup)
    # Parse!
    args = parser.parse_args()
    args.func(args)

# EOF
