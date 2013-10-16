import sys

# Modules are a bit weird in Plex...

import media_server
sys.modules['plex_api.media_server'] = media_server


import activity
sys.modules['plex_api.activity'] = activity

import activity_logging
sys.modules['plex_api.activity_logging'] = activity_logging

import activity_websocket
sys.modules['plex_api.activity_websocket'] = activity_websocket
