from plugin.core.enums import ActivityMode
from plugin.core.helpers.variable import pms_path

PLUGIN_NAME = 'Plex-Trakt-Scrobbler'
PLUGIN_IDENTIFIER = 'com.plexapp.plugins.trakttv'
PLUGIN_PREFIX = '/video/trakt'

PLUGIN_VERSION_BASE = (1, 0, 0, 2)
PLUGIN_VERSION_BRANCH = 'beta'

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
