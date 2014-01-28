#!/usr/bin/env python
# @file   raspi-config.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   17.03.2013

from glob import glob
import os

# Fabric stuff
from fabric.api import task, local, env, run, sudo, settings#, abort
from fabric.operations import put
from fabric.context_managers import hide, cd

# My stuff
from utils import dir_exists, to_boolean

############################################################
# Configuration
############################################################
env.hosts = ['pi@192.168.1.120']

simple_install = True

dirs_to_make        = ['~/src', '~/runtime']
things_to_download  = []
apt_repos           = []
packages_to_install = ['git', 'python-software-properties', 'python-pip', 'ca-certificates']
easy_install_list   = ['flexget']
git_repositories    = ['https://github.com/MilhouseVH/bcmstat.git', 'https://github.com/pilluli/service.xbmc.callbacks.git']
if not simple_install:
    apt_repos           = ['ppa:keithw/mosh']
    # For deluge from source
    #python-twisted
    #python-twisted-web
    #python-openssl
    #python-simplejson
    #python-setuptools
    #intltool
    #python-xdg
    #python-chardet
    #geoip-database
    #python-libtorrent
    #python-notify
    #python-pygame
    #python-glade2
    #librsvg2-common
    #xdg-utils
    #python-mako

# Utils
#sudo apt-get install localepurge
#sudo localepurge

############################################################
# Tasks
############################################################
@task
def deploy_ssh(remove_banner=True):
    with settings(warn_only=True):
        # Remove annoying Debian banner
        if remove_banner and run("test -f /etc/motd"):
            sudo("mv /etc/motd /etc/motd.bak")
        # Add our public keys
        if not dir_exists('~/.ssh'):
            # TODO: Cleanup keys and remove the test -d
            for key in glob("pubkeys/*.pub"):
                for host in env.hosts:
                    local('ssh-copy-id -l -i {0} {1}'.format(key, host))

@task
def prepare_dirs():
    dir_list = []
    for d in dirs_to_make:
        if not dir_exists(d):
            dir_list.append(d)
    if dir_list:
        run("mkdir {0}".format(" ".join(['%s' % dir_ for dir_ in dir_list])))

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

@task
def deploy_software(update=True):
    prepare_dirs()
    download_things()
    prepare_apt_repos()
    install_packages(update)
    install_python_packages()
    clone_git_repos()

@task
def deploy(update=True):
    deploy_ssh()
    deploy_software(update)

if __name__ == '__main__':
    deploy()

# EOF