from core.helpers import is_number
from plex.activity import ActivityMethod, PlexActivity
from log_sucker import LogSucker


LOG_REGEXP = Regex('(?P<key>\w*?)=(?P<value>\w+\w?)')


class Logging(ActivityMethod):
    name = 'Logging'

    log_path = None

    @classmethod
    def get_path(cls):
        if not cls.log_path:
            cls.log_path = Core.storage.join_path(Core.log.handlers[1].baseFilename, '..', '..', 'Plex Media Server.log')
            cls.log_path = Core.storage.abs_path(cls.log_path)

            Log.Info('log_path = "%s"' % cls.log_path)

        return cls.log_path

    @classmethod
    def test(cls):
        try:
            LogSucker.read(cls.get_path(), first_read=True)
            return True

        except Exception, ex:
            Log.Warn(str(ex))
            Log.Warn('%s method not available' % cls.name)

            return False

    def run(self):
        log_data = LogSucker.read(self.get_path(), True)

        while 1:
            if not Dict["scrobble"]:
                break

            # Grab the next line of the log
            log_data = LogSucker.read(self.get_path(), False, log_data['where'])

            self.process(dict(LOG_REGEXP.findall(log_data['line'])))

    def process(self, log_values):
        if not log_values:
            return

        Log.Debug(log_values)

        key = log_values.get('key') or log_values.get('ratingKey')

        if is_number(key):
            log_values['key'] = key
            log_values['state'] = log_values.get('state', 'playing')  # Assume playing if a state doesn't exist
        #    watch_or_scrobble(log_values)


PlexActivity.register(Logging)
