import sys

# submodules for Plex plugins "hack"

import client
sys.modules['data.client'] = client

import sync_status
sys.modules['data.sync_status'] = sync_status

import user
sys.modules['data.user'] = user

import watch_session
sys.modules['data.watch_session'] = watch_session
