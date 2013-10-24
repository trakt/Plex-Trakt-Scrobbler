from core.helpers import all
from plex.media_server import PlexMediaServer
from pts.activity import ActivityMethod, PlexActivity
from pts.scrobbler_logging import LoggingScrobbler
from log_sucker import LogSucker


CLIENT_REGEX = Regex(
    '^.*?Client \[(?P<client_id>.*?)\] reporting timeline state (?P<state>playing|stopped|paused), '
    'progress of (?P<time>\d+)/(?P<duration>\d+)ms for (?P<trailing>.*?)$'
)
CLIENT_PARAM_REGEX = Regex('(?P<key>\w+)=(?P<value>.*?)(?:,|\s|$)')


class Logging(ActivityMethod):
    name = 'Logging'
    required_info = ['ratingKey', 'state', 'time', 'duration']

    log_path = None

    def __init__(self, now_playing):
        super(Logging, self).__init__(now_playing)

        self.scrobbler = LoggingScrobbler()

    @classmethod
    def get_path(cls):
        if not cls.log_path:
            cls.log_path = Core.storage.join_path(Core.log.handlers[1].baseFilename, '..', '..', 'Plex Media Server.log')
            cls.log_path = Core.storage.abs_path(cls.log_path)

            Log.Info('log_path = "%s"' % cls.log_path)

        return cls.log_path

    @classmethod
    def test(cls):
        # Try enable logging
        if not PlexMediaServer.set_logging_state(True):
            Log.Warn('Unable to enable logging')

        # Test if logging is enabled
        if not PlexMediaServer.get_logging_state():
            Log.Warn('Debug logging not enabled, unable to use logging activity method.')
            return False

        # TODO would rather do real checks here instead of try/except
        try:
            LogSucker.read(cls.get_path(), first_read=True)
            return True
        except:
            Log.Warn(str(ex))

        return False

    def run(self):
        log_data = LogSucker.read(self.get_path(), True)

        while 1:
            if not Dict["scrobble"]:
                break

            # Grab the next line of the log
            log_data = LogSucker.read(self.get_path(), False, log_data['where'])

            self.process(log_data['line'])

    def process(self, line):
        match = CLIENT_REGEX.match(line)
        if not match:
            return

        info = match.groupdict()

        if info.get('trailing'):
            info.update(dict(CLIENT_PARAM_REGEX.findall(info.pop('trailing'))))

        valid = all([key in info for key in self.required_info])

        if valid:
            self.scrobbler.update(info)

PlexActivity.register(Logging)
