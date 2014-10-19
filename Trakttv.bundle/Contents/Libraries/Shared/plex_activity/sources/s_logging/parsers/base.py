from plex_activity.core.helpers import str_format

from pyemitter import Emitter
import logging
import re
import urlparse

log = logging.getLogger(__name__)

LOG_PATTERN = r'^.*?\[\w+\]\s\w+\s-\s{message}$'
REQUEST_HEADER_PATTERN = str_format(LOG_PATTERN, message=r"Request: (\[(?P<address>.*?):(?P<port>\d+)\]\s)?{method} {path}.*?")

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

IGNORE_REGEX = re.compile(str_format(LOG_PATTERN, message='(%s)' % ('|'.join('(%s)' % x for x in IGNORE_PATTERNS))), re.IGNORECASE)


PARAM_REGEX = re.compile(str_format(LOG_PATTERN, message=r' \* (?P<key>.*?) =\> (?P<value>.*?)'), re.IGNORECASE)


class Parser(Emitter):
    def __init__(self, core):
        self.core = core

    def read_parameters(self, *match_functions):
        match_functions = [self.parameter_match] + list(match_functions)

        info = {}

        while True:
            line = self.core.read_line_retry(timeout=5)
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
                log.debug('break on "%s"', line.strip())
                break

        return info

    def process(self, line):
        raise NotImplementedError()

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
