import sys

# submodules for Plex plugins "hack"

import base
sys.modules['sync.base'] = base

import push
sys.modules['sync.push'] = push

import pull
sys.modules['sync.pull'] = pull

import synchronize
sys.modules['sync.synchronize'] = synchronize

import manager
sys.modules['sync.manager'] = manager

import legacy
sys.modules['sync.legacy'] = legacy
