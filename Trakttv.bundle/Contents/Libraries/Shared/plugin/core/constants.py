from plugin.core.enums import ActivityMode

PLUGIN_NAME = 'Plex-Trakt-Scrobbler'
PLUGIN_IDENTIFIER = 'com.plexapp.plugins.trakttv'
PLUGIN_PREFIX = '/video/trakt'

PLUGIN_VERSION_BASE = (0, 9, 10, 5)
PLUGIN_VERSION_BRANCH = 'develop'

PLUGIN_VERSION = ''.join([
    '.'.join([str(x) for x in PLUGIN_VERSION_BASE]),
    '-' + PLUGIN_VERSION_BRANCH if PLUGIN_VERSION_BRANCH else ''
])

ACTIVITY_MODE = {
    ActivityMode.Automatic: None,
    ActivityMode.Logging:   ['logging'],
    ActivityMode.WebSocket: ['websocket']
}
