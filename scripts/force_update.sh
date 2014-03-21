#!/bin/bash
sudo -s
cd /scripts/upd_sys
rm *.sh
wget http://svn.stmlabs.com/svn/raspbmc/release/update-system/getfile.sh
wget http://svn.stmlabs.com/svn/raspbmc/release/update-system/cdn_env_prep.sh
reboot