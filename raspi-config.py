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
from utils import dirExists

############################################################
# Configuration
############################################################
env.hosts = ['pi@192.168.1.120']

packagesToInstall = ['git', 'rtorrent']
easyInstallList   = ['cheetah']
gitRepositories   = ['git://github.com/midgetspy/Sick-Beard.git']

############################################################
# Tasks
############################################################
@task
def deploySSH(removeBanner=True):
    with settings(warn_only=True):
        # Remove annoying Debian banner
        if removeBanner and run("test -f /etc/motd"):
            sudo("mv /etc/motd /etc/motd.bak")
        # Add our public keys
        if not dirExists('~/.ssh'):
            # TODO: Cleanup keys and remove the test -d
            for key in glob("pubkeys/*.pub"):
                for host in env.hosts:
                    local('ssh-copy-id -i {0} {1}'.format(key, host))

@task
def prepareDirs():
    if not dirExists('~/src'):
        run("mkdir $HOME/src")

@task
def installPackages(update=True):
    with update and hide('stdout'):
        sudo('apt-get update')
    sudo('apt-get install -y {0}'.format(' '.join(packagesToInstall)))

@task
def installPythonPackages():
    # First, check if we have easy_install
    with settings(warn_only=True):
        if run('hash easy_install').failed:
            with cd('/home/pi/src'):
                with hide('stdout'):
                    run('wget --no-check-certificate https://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg#md5=fe1f997bc722265116870bc7919059ea')
                sudo('sh setuptools-0.6c11-py2.7.egg')
    # Now install packages
    for package in easyInstallList:
        sudo('easy_install {0}'.format(package))

@task
def cloneGitRepos():
    with settings(warn_only=True):
        with cd('$HOME/src'):
            for repo in gitRepositories:
                name = os.path.splitext(os.path.split(repo)[1])[0]
                if run('test -d {0}'.format(name)).failed:
                    run('git clone {0}'.format(repo))

@task
def deploySoftware(update=True):
    prepareDirs()
    installPackages(update)
    installPythonPackages()
    cloneGitRepos()

@task
def deploy(update=True):
    deploySSH()
    deploySoftware(update)

if __name__ == '__main__':
    deploy()

# EOF