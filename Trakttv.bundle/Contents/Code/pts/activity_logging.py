from core.eventing import EventManager
from core.helpers import str_format
from core.logger import Logger
from plex.plex_media_server import PlexMediaServer
from plex.plex_preferences import PlexPreferences
from pts.activity import ActivityMethod, Activity
from asio_base import SEEK_ORIGIN_CURRENT
from asio import ASIO
import time
import os

LOG_PATTERN = r'^.*?\[\w+\]\s\w+\s-\s{message}$'
REQUEST_HEADER_PATTERN = str_format(LOG_PATTERN, message=r"Request: (\[(?P<address>.*?):(?P<port>\d+)\]\s)?{method} {path}.*?")

PLAYING_HEADER_REGEX = Regex(str_format(REQUEST_HEADER_PATTERN, method="GET", path="/:/(?P<type>timeline|progress)"))

IGNORE_PATTERNS = [
    r'error parsing allowedNetworks.*?',
    r'Comparing request from.*?',
    r'We found auth token (.*?), enabling token-based authentication\.',
    r'Came in with a super-token, authorization succeeded\.',
    r'Refreshing tokens inside the token-based authentication filter.',
    r'Play progress on .*? - got played .*? ms by account .*?!'
]

IGNORE_REGEX = Regex(str_format(LOG_PATTERN, message='(%s)' % ('|'.join('(%s)' % x for x in IGNORE_PATTERNS))))

PARAM_REGEX = Regex(str_format(LOG_PATTERN, message=r' \* (?P<key>.*?) =\> (?P<value>.*?)'))
RANGE_REGEX = Regex(str_format(LOG_PATTERN, message=r'Request range: \d+ to \d+'))
CLIENT_REGEX = Regex(str_format(LOG_PATTERN, message=r'Client \[(?P<machineIdentifier>.*?)\].*?'))

NOW_USER_REGEX = Regex(str_format(LOG_PATTERN, message=r'\[Now\] User is (?P<user_name>.+) \(ID: (?P<user_id>\d+)\)'))
NOW_CLIENT_REGEX = Regex(str_format(LOG_PATTERN, message=r'\[Now\] Device is (?P<client>.+)\.'))

log = Logger('pts.activity_logging')


class LoggingActivity(ActivityMethod):
    name = 'LoggingActivity'

    required_info = [
        'ratingKey',
        'state', 'time'
    ]

    extra_info = [
        'duration',

        'user_name', 'user_id',
        'machineIdentifier', 'client'
    ]

    log_path = None
    log_file = None

    @classmethod
    def get_path(cls):
        if not cls.log_path:
            cls.log_path = os.path.join(Core.log.handlers[1].baseFilename, '..', '..', 'Plex Media Server.log')
            cls.log_path = os.path.abspath(cls.log_path)

            log.debug('log_path = "%s"' % cls.log_path)

        return cls.log_path

    @classmethod
    def test(cls):
        # Try enable logging
        if not PlexPreferences.log_debug(True):
            log.warn('Unable to enable logging')

        # Test if logging is enabled
        if not PlexPreferences.log_debug():
            log.warn('Debug logging not enabled, unable to use logging activity method.')
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
            log.info('Opened file path: "%s"' % cls.log_path)

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
                log.debug("Log file moved (probably rotated), closing")
                cls.close()

            # If we are below max_interval, keep increasing the interval
            if retry_interval < max_interval:
                retry_interval = retry_interval * interval_step

                # Ensure the new retry_interval is below max_interval
                if retry_interval > max_interval:
                    retry_interval = max_interval

            # Sleep if we should still retry
            if try_count <= max_tries:
                if try_count > 1:
                    log.debug('Log file read returned nothing, waiting %.02f seconds and then trying again' % retry_interval)
                    time.sleep(retry_interval)

                # Ping server to see if server is still active
                PlexMediaServer.get_info(quiet=True)

        if line and try_count > 2:
            log.debug('Successfully read the log file after retrying')
        elif not line:
            log.warn('Finished retrying, still no success')

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
            log.warn('Unable to read log file')
            return

        log.debug('Ready')

        while True:
            # Grab the next line of the log
            line = self.try_read_line(timeout=60)

            if line:
                self.process(line)
            else:
                log.warn('Unable to read log file')

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
            log.warn('Unknown activity type "%s"', activity_type)
            return

        # Ensure we successfully matched a result
        if not match:
            return

        # Sanitize the activity result
        info = {
            'address': header_match.group('address'),
            'port': header_match.group('port')
        }

        # - Get required info parameters
        for key in self.required_info:
            if key in match and match[key] is not None:
                info[key] = match[key]
            else:
                log.warn('Invalid activity match, missing key %s (%s)', key, match)
                return

        # - Add in any extra info parameters
        for key in self.extra_info:
            if key in match:
                info[key] = match[key]
            else:
                info[key] = None

        # Update the scrobbler with the current state
        EventManager.fire('scrobbler.logging.update', info)

    def timeline(self):
        return self.read_parameters(
            lambda line: self.regex_match(CLIENT_REGEX, line),
            lambda line: self.regex_match(RANGE_REGEX, line),

            # [Now]* entries
            lambda line: self.regex_match(NOW_USER_REGEX, line),
            lambda line: self.regex_match(NOW_CLIENT_REGEX, line),
        )

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
                log.warn('Unable to read log file')
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
                log.debug('break on "%s"', line)
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
    def regex_match(regex, line):
        match = regex.match(line.strip())
        if not match:
            return None

        return match.groupdict()


Activity.register(LoggingActivity, weight=1)
