import sys

# submodules for Plex plugins "hack"

import plex_objects
sys.modules['plex.plex_objects'] = plex_objects

import plex_base
sys.modules['plex.plex_base'] = plex_base

import metadata
sys.modules['plex.metadata'] = metadata

import media_server
sys.modules['plex.media_server'] = media_server

import media_server_new
sys.modules['plex.media_server_new'] = media_server_new
