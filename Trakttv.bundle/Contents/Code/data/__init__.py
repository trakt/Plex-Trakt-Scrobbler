import sys

# submodules for Plex plugins "hack"

import client
sys.modules['data.client'] = client

import user
sys.modules['data.user'] = user

import watch_session
sys.modules['data.watch_session'] = watch_session
