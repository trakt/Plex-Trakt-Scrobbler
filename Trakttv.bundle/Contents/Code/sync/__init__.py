import sys

# submodules for Plex plugins "hack"

import sync_base
sys.modules['sync.sync_base'] = sync_base

import sync_task
sys.modules['sync.sync_task'] = sync_task

import push
sys.modules['sync.push'] = push

import pull
sys.modules['sync.pull'] = pull

import synchronize
sys.modules['sync.synchronize'] = synchronize

import sync_statistics
sys.modules['sync.sync_statistics'] = sync_statistics

import sync_manager
sys.modules['sync.sync_manager'] = sync_manager
