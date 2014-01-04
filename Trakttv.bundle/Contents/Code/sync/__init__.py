import sys

# submodules for Plex plugins "hack"

import sync_base
sys.modules['sync.sync_base'] = sync_base

import task
sys.modules['sync.task'] = task

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
