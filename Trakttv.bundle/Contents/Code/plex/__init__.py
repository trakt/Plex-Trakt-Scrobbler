import sys

# Modules are a bit weird in Plex...

import media_server
sys.modules['plex.media_server'] = media_server


import scrobbler_websocket
sys.modules['plex.scrobbler_websocket'] = scrobbler_websocket


import activity
sys.modules['plex.activity'] = activity

import activity_logging
sys.modules['plex.activity_logging'] = activity_logging

import activity_websocket
sys.modules['plex.activity_websocket'] = activity_websocket
