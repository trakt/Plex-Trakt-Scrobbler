PLUGIN_NAME = 'Plex-Trakt-Scrobbler'

PLUGIN_VERSION_BASE = (0, 7, 11)
PLUGIN_VERSION_BRANCH = 'syncing-2.0'

PLUGIN_VERSION = ''.join([
    '.'.join([str(x) for x in PLUGIN_VERSION_BASE]),
    '-' + PLUGIN_VERSION_BRANCH if PLUGIN_VERSION_BRANCH else ''
])

NAME = L('Title')
ART = 'art-default.jpg'
ICON = 'icon-default.png'
