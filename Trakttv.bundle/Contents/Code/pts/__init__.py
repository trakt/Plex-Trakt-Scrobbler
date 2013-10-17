import sys

# Modules? what are they?

import scrobbler
sys.modules['pts.scrobbler'] = scrobbler

import scrobbler_logging
sys.modules['pts.scrobbler_logging'] = scrobbler_logging

import scrobbler_websocket
sys.modules['pts.scrobbler_websocket'] = scrobbler_websocket

import activity
sys.modules['pts.activity'] = activity

import activity_logging
sys.modules['pts.activity_logging'] = activity_logging

import activity_websocket
sys.modules['pts.activity_websocket'] = activity_websocket
