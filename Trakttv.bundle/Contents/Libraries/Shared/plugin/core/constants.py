PLUGIN_NAME = 'Plex-Trakt-Scrobbler'
PLUGIN_IDENTIFIER = 'com.plexapp.plugins.trakttv'
PLUGIN_PREFIX = '/video/trakt'

PLUGIN_VERSION_BASE = (0, 9, 1, 12)
PLUGIN_VERSION_BRANCH = 'beta'

PLUGIN_VERSION = ''.join([
    '.'.join([str(x) for x in PLUGIN_VERSION_BASE]),
    '-' + PLUGIN_VERSION_BRANCH if PLUGIN_VERSION_BRANCH else ''
])

ACTIVITY_MODE = {
    'Automatic':            None,
    'Logging (Legacy)':     ['LoggingActivity', 'LoggingScrobbler'],
    'WebSocket (PlexPass)': ['WebSocketActivity', 'WebSocketScrobbler']
}
