from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH, PMS_PATH
from plugin.core.exceptions import ConnectionError
from plugin.core.helpers.error import ErrorHasher
from plugin.managers.core.base import Manager, Create
from plugin.managers.message import MessageManager
from plugin.models.exception import Exception
from plugin.models.message import Message

from datetime import datetime
from requests import exceptions as requests_exceptions
from requests.packages.urllib3 import exceptions as urllib3_exceptions
from six.moves.urllib.parse import urlparse
import logging
import os
import re
import socket
import ssl
import sys
import trakt

VERSION_BASE = '.'.join([str(x) for x in PLUGIN_VERSION_BASE])
VERSION_BRANCH = PLUGIN_VERSION_BRANCH

RE_TRACEBACK = re.compile(r"\w+ \(most recent call last\)\:\n(?P<traceback>(?:.*?\n)*)(?P<type>\w+)\: (?P<message>.*?)(?:\n|$)", re.IGNORECASE)

FINAL_EXCEPTION_TYPES = [
    urllib3_exceptions.ConnectTimeoutError,
    urllib3_exceptions.ProxyError
]

log = logging.getLogger(__name__)


class CreateException(Create):
    #
    # exc_info
    #

    def from_exc_info(self, exc_info=None):
        if exc_info is None:
            # Retrieve `exc_info` of last exception
            exc_info = sys.exc_info()

        # Parse exception
        message_type = Message.Type.Exception

        try:
            message_type, exc_info = self._parse_exception(exc_info)
        except Exception as ex:
            log.warn('Unable to parse exception: %s', ex, exc_info=True)

        # Create exception
        exception = self.model(
            type=ErrorHasher.exc_type(exc_info[0]),
            message=ErrorHasher.exc_message(exc_info[1]),
            traceback=ErrorHasher.exc_traceback(exc_info[2]),

            timestamp=datetime.utcnow(),
            version_base=VERSION_BASE,
            version_branch=VERSION_BRANCH
        )

        # Calculate exception hash
        exception.hash = ErrorHasher.hash(
            exception,
            include_traceback=message_type == Message.Type.Exception
        )

        # Create/Lookup message for exception
        exception.error = MessageManager.get.from_exception(
            exception,
            message_type=message_type
        )

        # Save exception details
        exception.save()

        return exception, exception.error

    #
    # message
    #

    def from_message(self, message):
        match = RE_TRACEBACK.match(message)

        if match is None:
            return

        # Create exception
        exception = self.model(
            type=match.group('type'),
            message=match.group('message'),
            traceback=self.strip_traceback(match.group('traceback')),

            timestamp=datetime.utcnow(),
            version_base=VERSION_BASE,
            version_branch=VERSION_BRANCH
        )

        # Calculate exception hash
        exception.hash = ErrorHasher.hash(exception)

        # Create/Lookup message for exception
        exception.error = MessageManager.get.from_exception(exception)

        # Save exception details
        exception.save()

        return exception, exception.error

    @staticmethod
    def strip_traceback(tb):
        lines = tb.split('\n')

        for x in xrange(len(lines)):
            line = lines[x]

            if not line.startswith('  File'):
                continue

            try:
                # Try find path start/end quotes
                path_start = line.index('"') + 1
                path_end = line.index('"', path_start)
            except ValueError:
                # Unable to find path quotes
                continue

            # Convert path to relative
            path = os.path.relpath(line[path_start:path_end], PMS_PATH)

            # Update line
            lines[x] = line[:path_start] + path + line[path_end:]

        return '\n'.join(lines)

    def _parse_exception(self, exc_info):
        if type(exc_info) is not tuple or len(exc_info) != 3:
            return Message.Type.Exception, exc_info

        # Parse exception
        _, ex, tb = exc_info

        if isinstance(ex, trakt.RequestError):
            return self._parse_trakt_error(exc_info)

        if isinstance(ex, requests_exceptions.RequestException):
            return self._parse_request_exception(exc_info)

        return Message.Type.Exception, exc_info

    def _parse_trakt_error(self, exc_info):
        if type(exc_info) is not tuple or len(exc_info) != 3:
            return Message.Type.Exception, exc_info

        # Parse exception information
        _, ex, tb = exc_info

        if not isinstance(ex, trakt.RequestError):
            return Message.Type.Exception, exc_info

        # Construct connection error
        return Message.Type.Trakt, (
            ConnectionError,
            ConnectionError(self._format_exception(ex)),
            tb
        )

    def _parse_request_exception(self, exc_info):
        if type(exc_info) is not tuple or len(exc_info) != 3:
            return Message.Type.Exception, exc_info

        # Parse exception information
        _, ex, tb = exc_info

        if not isinstance(ex, requests_exceptions.RequestException) or not ex.request:
            return Message.Type.Exception, exc_info

        # Parse request url
        url = urlparse(ex.request.url)

        if not url:
            return Message.Type.Exception, exc_info

        # Retrieve service title
        if url.netloc == 'sentry.skipthe.net':
            message_type = Message.Type.Sentry
        elif url.netloc == 'plex.tv' or url.netloc.endswith('.plex.tv'):
            message_type = Message.Type.Plex
        elif url.netloc == 'trakt.tv' or url.netloc.endswith('.trakt.tv'):
            message_type = Message.Type.Trakt
        else:
            return Message.Type.Exception, exc_info

        # Construct connection error
        return message_type, (
            ConnectionError,
            ConnectionError(self._format_exception(ex)),
            tb
        )

    @classmethod
    def _format_exception(cls, ex, include_type=True):
        ex = cls._find_inner_exception(ex)

        if isinstance(ex, urllib3_exceptions.ProxyError):
            return '%s: %s' % (
                type(ex).__name__,
                cls._format_exception(ex.args, include_type=False) or ex.message
            )

        # Trakt
        if isinstance(ex, trakt.RequestError):
            return '%s (code: %r)' % (
                ex.error[1],
                ex.status_code
            )

        # Socket
        if isinstance(ex, socket.error):
            if ex.errno is None:
                return '%s' % (
                    ex.message or ex.strerror
                )

            return '%s (code: %r)' % (
                ex.message or ex.strerror,
                ex.errno
            )

        # Generic exception
        if not include_type:
            return ex.message

        return '%s: %s' % (
            type(ex).__name__,
            ex.message
        )

    @classmethod
    def _find_inner_exception(cls, ex):
        # Find exceptions inside list or tuple
        if type(ex) is list or type(ex) is tuple:
            for value in ex:
                if not issubclass(value.__class__, BaseException):
                    continue

                return cls._find_inner_exception(value)

            return Exception('Unknown Error')

        # Ensure `ex` is an exception
        if not issubclass(ex.__class__, BaseException):
            return ex

        # Return final exceptions
        if type(ex) in FINAL_EXCEPTION_TYPES:
            return ex

        # Requests
        if isinstance(ex, requests_exceptions.RequestException):
            if len(ex.args) < 1:
                return ex

            return cls._find_inner_exception(ex.args)

        # urllib3
        if isinstance(ex, urllib3_exceptions.MaxRetryError):
            return cls._find_inner_exception(ex.reason)

        if isinstance(ex, urllib3_exceptions.HTTPError):
            if issubclass(ex.message.__class__, BaseException):
                return cls._find_inner_exception(ex.message)

            if len(ex.args) < 1:
                return ex

            return cls._find_inner_exception(ex.args)

        # Generic exception
        return ex


class ExceptionManager(Manager):
    create = CreateException

    model = Exception
