import sys

# submodules for Plex plugins "hack"
import sync_status
sys.modules['data.sync_status'] = sync_status
