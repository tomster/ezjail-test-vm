# coding: utf-8
from fabric.api import env
from bsdploy.fabric import bootstrap, fetch_assets

# shutup pyflakes
(bootstrap, fetch_assets)


env.shell = '/bin/sh -c'
