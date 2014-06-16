PLUGIN_NAME = 'Plex-Trakt-Scrobbler'
PLUGIN_IDENTIFIER = 'com.plexapp.plugins.trakttv'

PLUGIN_VERSION_BASE = (0, 8, 3, 6)
PLUGIN_VERSION_BRANCH = 'develop'

PLUGIN_VERSION = ''.join([
    '.'.join([str(x) for x in PLUGIN_VERSION_BASE]),
    '-' + PLUGIN_VERSION_BRANCH if PLUGIN_VERSION_BRANCH else ''
])

NAME = L('Title')
ART = 'art-default.jpg'
ICON = 'icon-default.png'

ACTIVITY_MODE = {
    'Automatic':            None,
    'Logging (Legacy)':     ['LoggingActivity', 'LoggingScrobbler'],
    'WebSocket (PlexPass)': ['WebSocketActivity', 'WebSocketScrobbler']
}