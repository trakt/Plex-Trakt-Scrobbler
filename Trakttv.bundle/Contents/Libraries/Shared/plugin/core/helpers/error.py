from plugin.core.constants import PMS_PATH

import hashlib
import os
import traceback


class ErrorHasher(object):
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
            (os.path.relpath(filename, PMS_PATH), line_num, name, line)
            for (filename, line_num, name, line) in tb_list
        ]))

    @classmethod
    def hash(cls, exception=None, exc_info=None, include_traceback=True):
        if exception is not None:
            # Retrieve hash parameters from `Exception` object
            type = exception.type
            message = exception.message
            tb = exception.traceback
        elif exc_info is not None:
            # Build hash parameters from `exc_info`
            type = cls.exc_type(exc_info[0])
            message = cls.exc_message(exc_info[1])
            tb = cls.exc_traceback(exc_info[2])
        else:
            raise ValueError

        m = hashlib.md5()
        m.update(str(type))
        m.update(str(message))

        if include_traceback:
            m.update(str(tb))

        return m.hexdigest()
