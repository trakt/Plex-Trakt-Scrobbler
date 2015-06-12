from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH
from plugin.managers.core.base import Manager, Create
from plugin.managers.message import MessageManager
from plugin.models.exception import Exception

import hashlib
import logging
import os
import re
import sys
import traceback

BASE_PATH = __file__[:__file__.lower().index('plug-ins')]
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
            type=self.exc_type(exc_info[0]),
            message=self.exc_message(exc_info[1]),
            traceback=self.exc_traceback(exc_info[2]),

            version_base=VERSION_BASE,
            version_branch=VERSION_BRANCH
        )

        # Calculate exception hash
        exception.hash = self.manager.hash(exception)

        # Create/Lookup message for exception
        exception.error = MessageManager.get.from_exception(exception)

        # Save exception details
        exception.save()

        return exception, exception.error

    @staticmethod
    def exc_type(type):
        return type.__name__

    @staticmethod
    def exc_message(exception):
        return getattr(exception, 'message', None)

    @staticmethod
    def exc_traceback(tb):
        """Format traceback with relative paths"""
        tb_list = traceback.extract_tb(tb)

        return ''.join(traceback.format_list([
            (os.path.relpath(filename, BASE_PATH), line_num, name, line)
            for (filename, line_num, name, line) in tb_list
        ]))

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

            version_base=VERSION_BASE,
            version_branch=VERSION_BRANCH
        )

        # Calculate exception hash
        exception.hash = self.manager.hash(exception)

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
            path = os.path.relpath(line[path_start:path_end], BASE_PATH)

            # Update line
            lines[x] = line[:path_start] + path + line[path_end:]

        return '\n'.join(lines)


class ExceptionManager(Manager):
    create = CreateException

    model = Exception

    @staticmethod
    def hash(exception):
        m = hashlib.md5()
        m.update(exception.type)
        m.update(exception.message)
        m.update(exception.traceback)

        return m.hexdigest()
