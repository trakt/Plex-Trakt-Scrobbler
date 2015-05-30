from plugin.core.constants import PLUGIN_VERSION_BASE, PLUGIN_VERSION_BRANCH
from plugin.models import Exception, Message, SyncResultError, SyncResultException

import hashlib
import logging
import os
import traceback

BASE_PATH = __file__[:__file__.lower().index('plug-ins')]

log = logging.getLogger(__name__)


class ExceptionLogger(object):
    version_base = '.'.join([str(x) for x in PLUGIN_VERSION_BASE])
    version_branch = PLUGIN_VERSION_BRANCH

    @classmethod
    def store(cls, exc_info):
        type = '.'.join([
            exc_info[0].__module__,
            exc_info[0].__name__
        ])

        message = getattr(exc_info[1], 'message', None)

        # Convert traceback paths to relative
        tb_list = traceback.extract_tb(exc_info[2])

        tb = ''.join(traceback.format_list([
            (os.path.relpath(filename, BASE_PATH), line_num, name, line)
            for (filename, line_num, name, line) in tb_list
        ]))

        # Create new exception object
        exception = cls._create_exception(type, message, tb)

        # Get (or create new) error matching the exception
        error = cls._create_error(exception)

        # Save remaining `exception` changes
        exception.save()

        return exception, error

    @classmethod
    def result_store(cls, result, exc_info):
        exception, error = cls.store(exc_info)

        # Link error to result
        SyncResultError.create(
            result=result,
            error=error
        )

        # Link exception to result
        SyncResultException.create(
            result=result,
            exception=exception
        )

    @classmethod
    def _create_error(cls, exception):
        # Find matching (or create new dummy) error message
        error = Message.get_or_create(
            type=Message.Type.Exception,
            exception_hash=exception.hash,

            version_base=cls.version_base,
            version_branch=cls.version_branch
        )

        if error.revision is None:
            # New error found, fill with details from exception
            error.summary = exception.message
            error.description = exception.traceback

            error.revision = 0
            error.save()

        # Update exception error
        exception.error = error

        return error

    @classmethod
    def _create_exception(cls, type, message, tb):
        # Create new exception object
        exception = Exception(
            type=type,
            message=message,
            traceback=tb,

            version_base=cls.version_base,
            version_branch=cls.version_branch
        )

        # Calculate exception hash, store in database
        exception.hash = cls._hash(exception)

        return exception

    @staticmethod
    def _hash(exception):
        m = hashlib.md5()
        m.update(exception.type)
        m.update(exception.message)
        m.update(exception.traceback)

        return m.hexdigest()
