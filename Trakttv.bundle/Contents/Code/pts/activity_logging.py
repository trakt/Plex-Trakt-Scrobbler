from core.helpers import all
from plex.media_server import PlexMediaServer
from pts.activity import ActivityMethod, PlexActivity
from pts.scrobbler_logging import LoggingScrobbler
from asio_base import SEEK_ORIGIN_CURRENT
from asio import ASIO
import time


CLIENT_REGEX = Regex(
    '^.*?Client \[(?P<client_id>.*?)\] reporting timeline state (?P<state>playing|stopped|paused), '
    'progress of (?P<time>\d+)/(?P<duration>\d+)ms for (?P<trailing>.*?)$'
)
CLIENT_PARAM_REGEX = Regex('(?P<key>\w+)=(?P<value>.*?)(?:,|\s|$)')


class Logging(ActivityMethod):
    name = 'Logging'
    required_info = ['ratingKey', 'state', 'time', 'duration']

    log_path = None
    log_file = None

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

        if cls.try_read_line(True):
            return True

        return False

    @classmethod
    def read_line(cls, timeout=30):
        if not cls.log_file:
            cls.log_file = ASIO.open(cls.get_path(), opener=False)
            cls.log_file.seek(cls.log_file.get_size(), SEEK_ORIGIN_CURRENT)
            cls.log_path = cls.log_file.get_path()
            print 'Opened file path: "%s"' % cls.log_path

        return cls.log_file.read_line(timeout=timeout, timeout_type='return')

    @classmethod
    def try_read_line(cls, start_interval=1, interval_step=1.6, max_interval=5, max_tries=4, timeout=30):
        line = None

        try_count = 0
        retry_interval = float(start_interval)

        while not line and try_count <= max_tries:
            try_count += 1

            line = cls.read_line(timeout)
            if line:
                break

            if cls.log_file.get_path() != cls.log_path:
                Log.Info("Log file moved (probably rotated), closing")
                cls.close()

            # If we are below max_interval, keep increasing the interval
            if retry_interval < max_interval:
                retry_interval = retry_interval * interval_step

                # Ensure the new retry_interval is below max_interval
                if retry_interval > max_interval:
                    retry_interval = max_interval

            # Sleep if we should still retry
            if try_count <= max_tries:
                Log.Info('Log file read returned nothing, waiting %.02f seconds and then trying again' % retry_interval)
                time.sleep(retry_interval)

        if line and try_count > 1:
            Log.Info('Successfully read the log file after retrying')
        elif not line:
            Log.Warn('Finished retrying, still no success')

        return line

    @classmethod
    def close(cls):
        if not cls.log_file:
            return

        cls.log_file.close()
        cls.log_file = None

    def run(self):
        line = self.try_read_line(timeout=60)
        if not line:
            Log.Warn('Unable to read log file')
            return

        while 1:
            if not Dict["scrobble"]:
                break

            # Grab the next line of the log
            line = self.try_read_line(timeout=60)

            if line:
                self.process(line)
            else:
                Log.Warn('Unable to read log file')

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
