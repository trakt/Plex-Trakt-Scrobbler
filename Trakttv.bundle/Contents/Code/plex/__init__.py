import sys

# submodules for Plex plugins "hack"

import plex_objects
sys.modules['plex.plex_objects'] = plex_objects

import plex_base
sys.modules['plex.plex_base'] = plex_base

import plex_matcher
sys.modules['plex.plex_matcher'] = plex_matcher

import plex_metadata
sys.modules['plex.plex_metadata'] = plex_metadata

import plex_preferences
sys.modules['plex.plex_preferences'] = plex_preferences

import plex_media_server
sys.modules['plex.plex_media_server'] = plex_media_server

import plex_library
sys.modules['plex.plex_library'] = plex_library
