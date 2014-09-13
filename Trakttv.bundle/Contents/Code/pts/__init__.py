import sys

# submodules for Plex plugins "hack"

import action_manager
sys.modules['pts.action_manager'] = action_manager

import scrobbler
sys.modules['pts.scrobbler'] = scrobbler

import scrobbler_logging
sys.modules['pts.scrobbler_logging'] = scrobbler_logging

import scrobbler_websocket
sys.modules['pts.scrobbler_websocket'] = scrobbler_websocket

import session_manager
sys.modules['pts.session_manager'] = session_manager
