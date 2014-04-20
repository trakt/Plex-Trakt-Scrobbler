import logging


class PlexHandler(logging.StreamHandler):
    level_funcs = {
        logging.DEBUG: Log.Debug,
        logging.INFO: Log.Info,
        logging.WARNING: Log.Warn,
        logging.ERROR: Log.Error,
        logging.CRITICAL: Log.Critical
    }

    def emit(self, record):
        func = self.level_funcs.get(record.levelno, Log.Debug)

        func('[%s] %s' % (record.name, self.format(record)))
