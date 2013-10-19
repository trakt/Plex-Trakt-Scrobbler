import sys

# Modules are a bit weird in Plex...
import media_server
sys.modules['plex.media_server'] = media_server
