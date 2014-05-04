#!/usr/bin/env python
# =============================================================================
# @file   backup.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   28.01.2014
# =============================================================================
"""XBMC backup utils."""

import os
import argparse

def do_backup(args):
    """Backup XBMC and deluge."""
    def perform_backup(origin_folder, output_file, service=None):
        """Backup folder.

        @arg  origin_folder: folder to backup
        @type origin_folder: str
        @arg  output_file: file to backup to
        @type output_file: str
        @arg  service: do I need to stop something?
        @type service: str

        """
        if os.path.exists(output_file):
            os.remove(output_file)
        base_folder, folder_to_backup = os.path.split(origin_folder)
        if service:
            os.system("sudo stop %s" % service)
        os.system("cd %s && tar -cvzf %s %s" % (base_folder, output_file, folder_to_backup))
        if service:
            os.system("sudo start %s" % service)
        print "Backed up to %s" % output_file

    output_folder = os.path.abspath(args.folder)
    for service in args.services:
        backup_file, backup_folder = all_services.get(service, (None, None))
        if backup_file is None:
            print "Unknown service %s" % service
            continue
        perform_backup(backup_folder, os.path.join(output_folder, backup_file), service)

def restore_backup(args):
    """Restore backup to  /home/pi/.xbmc.

    The tar file to restore is given by args.backup_folder.

    """
    def perform_restore(backup_file, output_folder, service=None):
        """Restore folder.

        @arg  backup_file: file to restore
        @type backup_file: str
        @arg  output_folder: file to restore to
        @type output_folder: str
        @arg  service: do I need to stop something?
        @type service: str

        """
        if not os.path.exists(backup_file):
            print "Cannot find backup file %s" % backup_file
            return
        base_folder, _ = os.path.split(output_folder)
        if service:
            os.system("sudo stop %s" % service)
        os.system("cd %s && tar -xzf %s" % (base_folder, backup_file))
        if service:
            os.system("sudo start %s" % service)
        print "Restored backup from %s" % backup_file

    backup_folder = os.path.abspath(args.folder)
    for service in args.services:
        backup_file, backup_folder = all_services.get(service, (None, None))
        if backup_file is None:
            print "Unknown service %s" % service
            continue
        perform_restore(os.path.join(backup_folder, backup_file), backup_folder, service)

all_services = {'xbmc'  : ('backup.xbmc.tar.gz', '/home/pi/.xbmc'),
                'deluge': ('backup.deluge.tar.gz', '/home/pi/.config/deluge')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    # Parser for the backup command
    backup_parser = subparsers.add_parser("backup")
    backup_parser.add_argument('folder', action='store', type=str, help="Folder to copy the backup file to")
    backup_parser.add_argument('services', action='store', type=str, nargs='+', default=['xbmc', 'deluge'], help="Services to backup")
    backup_parser.set_defaults(func=do_backup)
    # Parser for the restore command
    restore_parser = subparsers.add_parser("restore")
    restore_parser.add_argument('folder', action='store', type=str, help="Backup folder to restore from")
    restore_parser.add_argument('services', action='store', type=str, nargs='+', default=['xbmc', 'deluge'], help="Services to restore")
    restore_parser.set_defaults(func=restore_backup)
    # Parse!
    args = parser.parse_args()
    args.func(args)

# EOF
