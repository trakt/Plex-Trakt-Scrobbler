from plex import Plex
from plex_activity.sources.base import Source
from plex_activity.sources.s_logging.parsers import NowPlayingParser, ScrobbleParser

from asio import ASIO
from asio.file import SEEK_ORIGIN_CURRENT
from io import BufferedReader
import inspect
import logging
import os
import platform
import time

log = logging.getLogger(__name__)

PATH_HINTS = {
    'Linux': [
        '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log'
    ],
    'Windows': [
        lambda: os.path.join(os.getenv('LOCALAPPDATA'), 'Plex Media Server\\Logs\\Plex Media Server.log')
    ]
}


class Logging(Source):
    name = 'logging'
    events = [
        'logging.playing',
        'logging.action.played',
        'logging.action.unplayed'
    ]

    parsers = []
    path = None

    def __init__(self, activity):
        super(Logging, self).__init__()

        self.parsers = [p(self) for p in Logging.parsers]

        self.file = None
        self.reader = None

        self.path = None

        # Pipe events to the main activity instance
        self.pipe(self.events, activity)

    def run(self):
        line = self.read_line_retry(ping=True, stale_sleep=0.5)
        if not line:
            log.warn('Unable to read log file')
            return

        log.debug('Ready')

        while True:
            # Grab the next line of the log
            line = self.read_line_retry(ping=True)

            if line:
                self.process(line)
            else:
                log.warn('Unable to read log file')

    def process(self, line):
        for parser in self.parsers:
            if parser.process(line):
                return True

        return False

    def read_line(self):
        if not self.file:
            self.file = ASIO.open(self.get_path(), opener=False)
            self.file.seek(self.file.get_size(), SEEK_ORIGIN_CURRENT)

            self.reader = BufferedReader(self.file)

            self.path = self.file.get_path()
            log.info('Opened file path: "%s"' % self.path)

        return self.reader.readline()

    def read_line_retry(self, timeout=60, ping=False, stale_sleep=1.0):
        line = None
        stale_since = None

        while not line:
            line = self.read_line()

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
                if self.file.get_path() != self.path:
                    log.debug("Log file moved (probably rotated), closing")
                    self.close()
                elif ping:
                    # Ping server to see if server is still active
                    Plex.detail()
                    ping = False

            time.sleep(stale_sleep)

        return line

    def close(self):
        if not self.file:
            return

        self.reader.close()
        self.reader = None

        self.file.close()
        self.file = None

    @classmethod
    def get_path(cls):
        if cls.path:
            return cls.path

        hints = PATH_HINTS.get(platform.system())

        if hints is None:
            log.warn('Unknown system, unable to find log path')
            return None

        for hint in hints:
            if inspect.isfunction(hint):
                hint = hint()

            log.debug('Testing if "%s" exists', hint)

            if os.path.exists(hint):
                cls.path = hint
                break

        log.debug('path = "%s"' % cls.path)
        return cls.path


    @classmethod
    def test(cls):
        # TODO "Logging" source testing
        return True

    @classmethod
    def register(cls, parser):
        cls.parsers.append(parser)


Logging.register(NowPlayingParser)
Logging.register(ScrobbleParser)
