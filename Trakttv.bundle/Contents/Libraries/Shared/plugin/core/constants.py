from plugin.core.enums import ActivityMode
from plugin.core.helpers.variable import pms_path
from plugin.core.helpers.version import build_version

PLUGIN_NAME = 'Trakt.tv'
PLUGIN_ART = 'art-default.png'
PLUGIN_ICON = 'icon-default.png'
PLUGIN_IDENTIFIER = 'com.plexapp.plugins.trakttv'
PLUGIN_PREFIX = '/video/trakt'

PLUGIN_VERSION_BASE = (1, 3, 3)
PLUGIN_VERSION_BRANCH = 'master'

PLUGIN_VERSION = build_version(PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH)

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
