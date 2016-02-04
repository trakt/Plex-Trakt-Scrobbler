from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH, PMS_PATH
from plugin.core.helpers.error import ErrorHasher
from plugin.managers.core.base import Manager, Create
from plugin.managers.message import MessageManager
from plugin.models.exception import Exception

from datetime import datetime
import logging
import os
import re
import sys

VERSION_BASE = '.'.join([str(x) for x in PLUGIN_VERSION_BASE])
VERSION_BRANCH = PLUGIN_VERSION_BRANCH

RE_TRACEBACK = re.compile(r"\w+ \(most recent call last\)\:\n(?P<traceback>(?:.*?\n)*)(?P<type>\w+)\: (?P<message>.*?)(?:\n|$)", re.IGNORECASE)

log = logging.getLogger(__name__)


class CreateException(Create):
    #
    # exc_info
    #

    def from_exc_info(self, exc_info=None):
        if exc_info is None:
            # Retrieve `exc_info` of last exception
            exc_info = sys.exc_info()

        # Create exception
        exception = self.model(
            type=self.manager.exc_type(exc_info[0]),
            message=self.manager.exc_message(exc_info[1]),
            traceback=self.manager.exc_traceback(exc_info[2]),

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


class ExceptionManager(Manager):
    create = CreateException

    model = Exception
