from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH

from raven import Client
from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler
import logging
import platform


version = '.'.join([str(x) for x in PLUGIN_VERSION_BASE])

params = {
    'dsn': 'requests+http://0c21a23fd0444f32a40f9c36025d32c4:49c73b7803ca4c68be9a8d408cfe0913@sentry.skipthe.net/1',

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
