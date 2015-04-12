from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH

from raven import Client
from raven.handlers.logging import SentryHandler
import logging
import platform


version = '.'.join([str(x) for x in PLUGIN_VERSION_BASE])

params = {
    'dsn': 'requests+http://4d7f1fb6e69344cba94ea4c297d6409e:ea9dfc355773484da532cd7cd6ffdf3c@sentry.skipthe.net/1',

    'exclude_paths': [
        'com.plexapp.plugins.trakttv'
    ],
    'processors': [
        'raven.processors.RemoveStackLocalsProcessor',
        'plugin.raven.processors.RelativePathProcessor'
    ],

    'release': version,
    'tags': {
        # Plugin
        'plugin.version': version,
        'plugin.branch': PLUGIN_VERSION_BRANCH,

        # System
        'os.system': platform.system(),
        'os.release': platform.release(),
        'os.version': platform.version()
    }
}

# Build client
RAVEN = Client(**params)

# Setup logging
RAVEN_HANDLER = SentryHandler(RAVEN, level=logging.ERROR)
