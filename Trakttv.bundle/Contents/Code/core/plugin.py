PLUGIN_NAME = 'Plex-Trakt-Scrobbler'

PLUGIN_VERSION_BASE = (0, 6, 8)
PLUGIN_VERSION_BRANCH = 'develop'

PLUGIN_VERSION = ''.join([
    '.'.join([str(x) for x in PLUGIN_VERSION_BASE]),
    '-' + PLUGIN_VERSION_BRANCH if PLUGIN_VERSION_BRANCH else ''
])

NAME = L('Title')
ART = 'art-default.jpg'
ICON = 'icon-default.png'
