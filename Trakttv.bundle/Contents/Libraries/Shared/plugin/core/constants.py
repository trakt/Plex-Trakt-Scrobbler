from plugin.core.enums import ActivityMode
from plugin.core.helpers.variable import pms_path

PLUGIN_NAME = 'Trakt.tv'
PLUGIN_ART = 'art-default.png'
PLUGIN_ICON = 'icon-default.png'
PLUGIN_IDENTIFIER = 'com.plexapp.plugins.trakttv'
PLUGIN_PREFIX = '/video/trakt'

PLUGIN_VERSION_BASE = (1, 1, 0, 7)
PLUGIN_VERSION_BRANCH = 'develop'

PLUGIN_VERSION = ''.join([
    '.'.join([str(x) for x in PLUGIN_VERSION_BASE]),
    '-' + PLUGIN_VERSION_BRANCH if PLUGIN_VERSION_BRANCH else ''
])

PMS_PATH = pms_path()

ACTIVITY_MODE = {
    ActivityMode.Automatic: None,
    ActivityMode.Logging:   ['logging'],
    ActivityMode.WebSocket: ['websocket']
}

GUID_SERVICES = [
    'imdb',
    'tvdb',
    'tmdb',
    'tvrage'
]
