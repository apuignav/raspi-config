#!/usr/bin/env python
# @file   raspi-config.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   17.03.2013

import os

# Fabric stuff
from fabric.api import task, local, env, run, sudo, settings#, abort
from fabric.context_managers import hide, cd

# My stuff
from utils import dir_exists, file_exists, to_boolean

############################################################
# Configuration
############################################################
env.hosts = ['pi@192.168.1.120']

simple_install = True

dirs_to_make        = ['~/src', '~/runtime', '~/runtime/watch']
things_to_download  = []
apt_repos           = []
packages_to_install = ['git',
                       'python-software-properties',
                       'python-pip',
                       'python-dev',
                       'ca-certificates',
                       'lsof',
                       'python-lxml',
                       'mailutils',
                       'sendmail',
                       'smartmontools',
                       'curl',
                       'nmon',
                       'deluge-console',
                       # 'beautifulsoup',
                       #'iotop',
                      ]
# For psutil
# http://raspberrypi.stackexchange.com/questions/8566/peerguardian-moblock-installation-on-raspbmc
easy_install_list   = ['-e "git+git://github.com/seatgeek/fuzzywuzzy.git#egg=fuzzywuzzy"',
                       "speedtest-cli",
                       "xbmc-json",
                       "validictory",
                       "pebble",
                       "python-Levenshtein",
                       '"git+git://github.com/apuignav/pibullet.git"',
                       #"psutil",
                       ]
git_repositories    = [#'https://github.com/MilhouseVH/bcmstat.git',
                       #'https://github.com/pilluli/service.xbmc.callbacks.git',
                       #'https://github.com/amet/script.xbmc.subtitles.git',
                       'https://github.com/apuignav/raspi-config.git',
                       'https://github.com/apuignav/expense-bot.git']
if not simple_install:
    apt_repos           = ['ppa:keithw/mosh']

# For monitorix
# wget http://apt.izzysoft.de/izzysoft.asc
# sudo apt-key add izzysoft.asc
# add
#     deb [arch=all] http://apt.izzysoft.de/ubuntu generic universe
# to /etc/apt/sources.list
# sudo apt-get update
# sudo apt-get install monitorix


############################################################
# Tasks
############################################################
@task
def deploy_ssh(remove_banner=True):
    with settings(warn_only=True):
        # Remove annoying Debian banner
        if remove_banner:
            run('touch $HOME/.hushlogin')
        # Add our public keys
        if not dir_exists('~/.ssh'):
            for host in env.hosts:
                local('ssh-copy-id %s' % host)

@task
def prepare_dirs():
    dir_list = []
    for d in dirs_to_make:
        if not dir_exists(d):
            dir_list.append(d)
    if dir_list:
        run("mkdir {0}".format(" ".join(['%s' % dir_ for dir_ in dir_list])))
    with cd('/home/pi'):
        run('ln -sf /media/RaspiHD/ .')

@task
def download_things():
    for url in things_to_download:
        with cd('/home/pi/src'):
            run('wget --no-check-certificate %s' % url)

@task
def prepare_apt_repos():
    for repo in apt_repos:
        sudo('sudo add-apt-repository %s' % repo)

@task
def install_packages(update=True):
    update = to_boolean(update)
    if update:
        with hide('stdout'):
            sudo('apt-get update')
    print "Installing software"
    with hide('stdout'):
        sudo('apt-get install -y {0}'.format(' '.join(packages_to_install)))

@task
def install_python_packages():
    # Now install packages
    for package in easy_install_list:
        print "Installing %s" % package
        with hide('stdout'):
            sudo('pip install {0}'.format(package))

@task
def clone_git_repos():
    with settings(warn_only=True):
        with cd('$HOME/src'):
            for repo in git_repositories:
                name = os.path.splitext(os.path.split(repo)[1])[0]
                if run('test -d {0}'.format(name)).failed:
                    run('git clone {0}'.format(repo))

#@task
#def configure_xbmc():
    #with settings(warn_only=True):
        #with cd('$HOME'):
            #run('ln -sf $HOME/src/script.xbmc.subtitles/script.xbmc.subtitles ~/.xbmc/addons/')
            #if file_exists('/media/RaspiHD/backup/backup.tar.gz'):
                #run('python src/raspi-config/scripts/backup.py restore /media/RaspiHD/backup/backup.tar.gz')

@task
def configure_deluge():
# sudo cp $HOME/src/raspi-config/deluge/logrotate.d_deluge /etc/logrotate.d/deluge
    with settings(warn_only=True):
        sudo("cp /home/pi/src/raspi-config/deluge/deluge.conf /etc/init/")
        sudo("cp /home/pi/src/raspi-config/deluge/deluge-webui.conf /etc/init/")
        sudo("mkdir -p /var/log/deluge && sudo chown -R pi:pi /var/log/deluge && sudo chmod -R 750 /var/log/deluge")
        sudo("cp /home/pi/src/raspi-config/deluge/logrotate.d_deluge /etc/logrotate.d/deluge")
        run("ln -sf /media/RaspiHD/torrent/completo/ /home/pi/runtime/")
        run("ln -sf /media/RaspiHD/torrent/download/ /home/pi/runtime/")
        run("ln -sf /media/RaspiHD/torrent/tv_shows.cache /home/pi/runtime/")
        sudo("start deluge")
        sudo("stop deluge")
        if file_exists('/media/RaspiHD/backup/backup.deluge.tar.gz'):
            run('python $HOME/src/raspi-config/scripts/backup.py restore /media/RaspiHD/backup/ deluge')

@task
def configure_mail():
    with settings(warn_only=True):
        sudo('echo "djkarras@gmail.com" > ~root/.forward')
        run('echo "djkarras@gmail.com" > ~/.forward')

@task
def configure_crontab():
    run("crontab /home/pi/src/raspi-config/config/crontab.pi")

@task
def deploy_software(update=True):
    prepare_dirs()
    download_things()
    prepare_apt_repos()
    install_packages(update)
    install_python_packages()
    clone_git_repos()

@task
def deploy_configuration():
    #configure_xbmc()
    configure_deluge()
    configure_mail()
    configure_crontab()

@task
def deploy(update=True):
    deploy_ssh()
    deploy_software(update)
    deploy_configuration()

if __name__ == '__main__':
    deploy()

# EOF
