import sys

# submodules for Plex plugins "hack"

import media_server
sys.modules['plex.media_server'] = media_server
