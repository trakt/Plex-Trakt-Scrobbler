import sys

# submodules for Plex plugins "hack"

import legacy
sys.modules['sync.legacy'] = legacy
