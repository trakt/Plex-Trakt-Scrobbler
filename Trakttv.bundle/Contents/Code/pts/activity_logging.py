from plex.media_server import PlexMediaServer
from pts.activity import ActivityMethod, PlexActivity
from pts.scrobbler_logging import LoggingScrobbler
from asio_base import SEEK_ORIGIN_CURRENT
from asio import ASIO
import time

LOG_PATTERN = r'^.*?\[\d+\]\s\w+\s-\s{message}$'
REQUEST_HEADER_PATTERN = LOG_PATTERN.format(message=r"Request: {method} {path}.*?")

PLAYING_HEADER_REGEX = Regex(REQUEST_HEADER_PATTERN.format(method="GET", path="/:/(?P<type>timeline|progress)"))

IGNORE_PATTERNS = [
    r'error parsing allowedNetworks.*?',
    r'Comparing request from.*?',
    r'We found auth token (.*?), enabling token-based authentication.'
]

IGNORE_REGEX = Regex(LOG_PATTERN.format(message='|'.join('(%s)' % x for x in IGNORE_PATTERNS)))

PARAM_REGEX = Regex(LOG_PATTERN.format(message=r' \* (?P<key>\w+) =\> (?P<value>.*?)'))
RANGE_REGEX = Regex(LOG_PATTERN.format(message=r'Request range: \d+ to \d+'))
CLIENT_REGEX = Regex(LOG_PATTERN.format(message=r'Client \[(?P<machineIdentifier>.*?)\].*?'))


class Logging(ActivityMethod):
    name = 'Logging'
    required_info = ['ratingKey', 'state', 'time']
    extra_info = ['duration', 'machineIdentifier']

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
            Log.Info('Opened file path: "%s"' % cls.log_path)

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
        header_match = PLAYING_HEADER_REGEX.match(line)
        if not header_match:
            return

        activity_type = header_match.group('type')

        # Get a match from the activity entries
        if activity_type == 'timeline':
            match = self.timeline()
        elif activity_type == 'progress':
            match = self.progress()
        else:
            Log.Warn('Unknown activity type "%s"', activity_type)
            return

        # Ensure we successfully matched a result
        if not match:
            return

        # Sanitize the activity result
        info = {}

        # - Get required info parameters
        for key in self.required_info:
            if key in match and match[key] is not None:
                info[key] = match[key]
            else:
                Log.Warn('Invalid activity match, missing key %s (%s)', (key, match))
                return

        # - Add in any extra info parameters
        for key in self.extra_info:
            if key in match:
                info[key] = match[key]
            else:
                info[key] = None

        # Update the scrobbler with the current state
        self.scrobbler.update(info)

    def timeline(self):
        return self.read_parameters(self.client_match, self.range_match)

    def progress(self):
        data = self.read_parameters()
        if not data:
            return None

        # Translate parameters into timeline-style form
        return {
            'state': data.get('state'),
            'ratingKey': data.get('key'),
            'time': data.get('time')
        }

    def read_parameters(self, *match_functions):
        match_functions = [self.parameter_match] + list(match_functions)

        info = {}

        while True:
            line = self.try_read_line(timeout=5)
            if not line:
                Log.Warn('Unable to read log file')
                return None

            # Run through each match function to find a result
            match = None
            for func in match_functions:
                match = func(line)

                if match is not None:
                    break

            # Update info dict with result, otherwise finish reading
            if match:
                info.update(match)
            elif match is None and IGNORE_REGEX.match(line.strip()) is None:
                break

        return info

    @staticmethod
    def parameter_match(line):
        match = PARAM_REGEX.match(line.strip())
        if not match:
            return None

        match = match.groupdict()

        return {match['key']: match['value']}

    @staticmethod
    def range_match(line):
        match = RANGE_REGEX.match(line.strip())
        if not match:
            return None

        return match.groupdict()

    @staticmethod
    def client_match(line):
        match = CLIENT_REGEX.match(line.strip())
        if not match:
            return None

        return match.groupdict()


PlexActivity.register(Logging)
