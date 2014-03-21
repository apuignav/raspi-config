#!/bin/bash
cd /scripts/upd_sys
sudo rm *.sh
sudo wget http://svn.stmlabs.com/svn/raspbmc/release/update-system/getfile.sh
sudo wget http://svn.stmlabs.com/svn/raspbmc/release/update-system/cdn_env_prep.sh
sudo reboot