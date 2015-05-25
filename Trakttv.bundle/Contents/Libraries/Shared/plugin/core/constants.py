PLUGIN_NAME = 'Plex-Trakt-Scrobbler'
PLUGIN_IDENTIFIER = 'com.plexapp.plugins.trakttv'
PLUGIN_PREFIX = '/video/trakt'

PLUGIN_VERSION_BASE = (0, 9, 1, 26)
PLUGIN_VERSION_BRANCH = 'master'

PLUGIN_VERSION = ''.join([
    '.'.join([str(x) for x in PLUGIN_VERSION_BASE]),
    '-' + PLUGIN_VERSION_BRANCH if PLUGIN_VERSION_BRANCH else ''
])

ACTIVITY_MODE = {
    'Automatic':            None,
    'Logging (Legacy)':     ['logging'],
    'WebSocket (PlexPass)': ['websocket']
}
