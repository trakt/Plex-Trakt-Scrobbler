from core.logging_reporter import RAVEN_HANDLER

import logging

LOGGERS = [
    'plex',
    'plex_activity',
    'plex_metadata',
    'plugin',
    'pyemitter',
    'raven',
    'requests',
    'trakt'
]

TRACE = 5


class PlexHandler(logging.StreamHandler):
    level_funcs = {
        logging.DEBUG: Log.Debug,
        logging.INFO: Log.Info,
        logging.WARNING: Log.Warn,
        logging.ERROR: Log.Error,
        logging.CRITICAL: Log.Critical
    }

    level_map = {
        'plex':             'libraries',
        'plex_activity':    'libraries',
        'plex_metadata':    'libraries',

        'raven':            'libraries',
        'requests':         'libraries',
        'trakt':            'libraries'
    }

    def emit(self, record):
        min_level = self.get_min_level(record.name)

        if record.levelno < min_level:
            return

        func = self.level_funcs.get(record.levelno, Log.Debug)

        func('[%s] %s' % (record.name, self.format(record)))

    @classmethod
    def get_min_level(cls, name):
        # Only take first dot-separated "fragment"
        end = name.find('.')

        if end != -1:
            name = name[:end]

        # Map logger name (if it exists)
        if name in cls.level_map:
            name = cls.level_map[name]

        # Try retrieve preference
        try:
            value = Prefs['level_%s' % name]
        except KeyError:
            # Default to "plugin" preference
            value = Prefs['level_plugin']

        # Parse labels into level attributes
        if value == 'ERROR':
            return logging.ERROR

        if value == 'WARN' or value == 'WARNING':
            return logging.WARNING

        if value == 'INFO':
            return logging.INFO

        if value == 'DEBUG':
            return logging.DEBUG

        if value == "TRACE":
            return TRACE

        Log.Warn('Unknown logging level "%s"', value)
        return logging.DEBUG


# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Set logger levels
for name in LOGGERS:
    logger = logging.getLogger(name)

    logger.setLevel(TRACE)
    logger.handlers = [PlexHandler(), RAVEN_HANDLER]
