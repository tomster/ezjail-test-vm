# coding: utf-8
from fabric.api import env
from bsdploy.fabric import bootstrap

# shutup pyflakes
(bootstrap, )


env.shell = '/bin/sh -c'
