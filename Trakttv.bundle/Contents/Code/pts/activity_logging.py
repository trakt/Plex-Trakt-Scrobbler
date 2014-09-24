from core.eventing import EventManager
from core.helpers import str_format
from core.logger import Logger
from plex.plex_media_server import PlexMediaServer
from plex.plex_preferences import PlexPreferences
from pts.activity import ActivityMethod, Activity

from asio import ASIO
from asio.file import SEEK_ORIGIN_CURRENT
from io import BufferedReader
import os
import time
import urlparse


LOG_PATTERN = r'^.*?\[\w+\]\s\w+\s-\s{message}$'
REQUEST_HEADER_PATTERN = str_format(LOG_PATTERN, message=r"Request: (\[(?P<address>.*?):(?P<port>\d+)\]\s)?{method} {path}.*?")

PLAYING_HEADER_PATTERN = str_format(REQUEST_HEADER_PATTERN, method="GET", path="/:/(?P<type>timeline|progress)/?(?:\?(?P<query>.*?))?\s")
PLAYING_HEADER_REGEX = Regex(PLAYING_HEADER_PATTERN)

IGNORE_PATTERNS = [
    r'error parsing allowedNetworks.*?',
    r'Comparing request from.*?',
    r'We found auth token (.*?), enabling token-based authentication\.',
    r'Came in with a super-token, authorization succeeded\.',
    r'Refreshing tokens inside the token-based authentication filter.',
    r'Play progress on .*? - got played .*? ms by account .*?!',
    r'Request: \[.*?\] (GET|PUT) /video/:/transcode/.*?',
    r'Received transcode session ping for session .*?'
]

IGNORE_REGEX = Regex(str_format(LOG_PATTERN, message='(%s)' % ('|'.join('(%s)' % x for x in IGNORE_PATTERNS))))

PARAM_REGEX = Regex(str_format(LOG_PATTERN, message=r' \* (?P<key>.*?) =\> (?P<value>.*?)'))
RANGE_REGEX = Regex(str_format(LOG_PATTERN, message=r'Request range: \d+ to \d+'))
CLIENT_REGEX = Regex(str_format(LOG_PATTERN, message=r'Client \[(?P<machineIdentifier>.*?)\].*?'))

NOW_USER_REGEX = Regex(str_format(LOG_PATTERN, message=r'\[Now\] User is (?P<user_name>.+) \(ID: (?P<user_id>\d+)\)'))
NOW_CLIENT_REGEX = Regex(str_format(LOG_PATTERN, message=r'\[Now\] Device is (?P<product>.+?) \((?P<client>.+)\)\.'))

log = Logger('pts.activity_logging')


class LoggingActivity(ActivityMethod):
    name = 'LoggingActivity'

    path = None
    file = None
    reader = None

    parsers = []

    def __init__(self):
        super(LoggingActivity, self).__init__()

        self.parsers = [o(self) for o in self.parsers]

    def run(self):
        line = self.try_read_line(ping=True, stale_sleep=0.5)
        if not line:
            log.warn('Unable to read log file')
            return

        log.debug('Ready')

        while True:
            # Grab the next line of the log
            line = self.try_read_line(ping=True)

            if line:
                self.process(line)
            else:
                log.warn('Unable to read log file')

    def process(self, line):
        for parser in self.parsers:
            if parser.process(line):
                cls = getattr(parser, '__class__')
                return

    @classmethod
    def get_path(cls):
        if not cls.path:
            cls.path = os.path.join(Core.log.handlers[1].baseFilename, '..', '..', 'Plex Media Server.log')
            cls.path = os.path.abspath(cls.path)

            log.debug('path = "%s"' % cls.path)

        return cls.path

    @classmethod
    def test(cls):
        # Try enable logging
        if not PlexPreferences.log_debug(True):
            log.warn('Unable to enable logging')

        # Test if logging is enabled
        if not PlexPreferences.log_debug():
            log.warn('Debug logging not enabled, unable to use logging activity method.')
            return False

        if cls.try_read_line(timeout=15, ping=True, stale_sleep=0.5):
            return True

        return False

    @classmethod
    def read_line(cls):
        if not cls.file:
            cls.file = ASIO.open(cls.get_path(), opener=False)
            cls.file.seek(cls.file.get_size(), SEEK_ORIGIN_CURRENT)

            cls.reader = BufferedReader(cls.file)

            cls.path = cls.file.get_path()
            log.info('Opened file path: "%s"' % cls.path)

        return cls.reader.readline()

    @classmethod
    def try_read_line(cls, timeout=60, ping=False, stale_sleep=1.0):
        line = None
        stale_since = None

        while not line:
            line = cls.read_line()

            if line:
                stale_since = None
                time.sleep(0.05)
                break

            if stale_since is None:
                stale_since = time.time()
                time.sleep(stale_sleep)
                continue
            elif (time.time() - stale_since) > timeout:
                return None
            elif (time.time() - stale_since) > timeout / 2:
                # Nothing returned for 5 seconds
                if cls.file.get_path() != cls.path:
                    log.debug("Log file moved (probably rotated), closing")
                    cls.close()
                elif ping:
                    # Ping server to see if server is still active
                    PlexMediaServer.get_info(quiet=True)

                    ping = False

            time.sleep(stale_sleep)

        return line

    @classmethod
    def close(cls):
        if not cls.file:
            return

        cls.reader.close()
        cls.reader = None

        cls.file.close()
        cls.file = None

    @classmethod
    def register(cls, parser):
        cls.parsers.append(parser)


class Parser(object):
    def __init__(self, core):
        self.core = core

    def read_parameters(self, *match_functions):
        match_functions = [self.parameter_match] + list(match_functions)

        info = {}

        while True:
            line = self.core.try_read_line(timeout=5)
            if not line:
                log.warn('Unable to read log file')
                return {}

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
                log.trace('break on "%s"', line)
                break

        return info

    def process(self, line):
        raise NotImplementError()

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

    @staticmethod
    def query(match, value):
        if not value:
            return

        try:
            parameters = urlparse.parse_qsl(value, strict_parsing=True)
        except ValueError:
            return

        for key, value in parameters:
            match.setdefault(key, value)


class NowPlayingParser(Parser):
    required_info = [
        'ratingKey',
        'state', 'time'
    ]

    extra_info = [
        'duration',

        'user_name', 'user_id',
        'machineIdentifier', 'client'
    ]

    def process(self, line):
        header_match = PLAYING_HEADER_REGEX.match(line)
        if not header_match:
            return False

        activity_type = header_match.group('type')

        # Get a match from the activity entries
        if activity_type == 'timeline':
            match = self.timeline()
        elif activity_type == 'progress':
            match = self.progress()
        else:
            log.warn('Unknown activity type "%s"', activity_type)
            return True

        if match is None:
            match = {}

        # Extend match with query info
        self.query(match, header_match.group('query'))

        # Ensure we successfully matched a result
        if not match:
            return True

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
                return True

        # - Add in any extra info parameters
        for key in self.extra_info:
            if key in match:
                info[key] = match[key]
            else:
                info[key] = None

        # Update the scrobbler with the current state
        EventManager.fire('scrobbler.logging.update', info)
        return True

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
            return {}

        # Translate parameters into timeline-style form
        return {
            'state': data.get('state'),
            'ratingKey': data.get('key'),
            'time': data.get('time')
        }


class ScrobbleParser(Parser):
    pattern = str_format(LOG_PATTERN, message=r'Library item (?P<rating_key>\d+) \'(?P<title>.*?)\' got (?P<action>(?:un)?played) by account (?P<account_key>\d+)!.*?')
    regex = Regex(pattern)

    def process(self, line):
        match = self.regex.match(line)
        if not match:
            return False

        EventManager.fire('plex.activity.scrobble', {
            'account_key': match.group('account_key'),
            'rating_key': match.group('rating_key'),

            'title': match.group('title'),
            'action': match.group('action'),
        })
        return True

# register parsers
LoggingActivity.register(NowPlayingParser)
LoggingActivity.register(ScrobbleParser)

# register activity method
Activity.register(LoggingActivity, weight=1)
