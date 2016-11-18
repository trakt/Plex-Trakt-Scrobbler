from plugin.managers.exception import ExceptionManager

from exception_wrappers import DisabledError
import logging

log = logging.getLogger(__name__)


class ErrorStorage(logging.Handler):
    def __init__(self):
        super(ErrorStorage, self).__init__()

    def emit(self, record):
        if record.levelno < logging.ERROR:
            return

        try:
            if record.exc_info:
                ExceptionManager.create.from_exc_info(record.exc_info)
                return

            self.format(record)

            ExceptionManager.create.from_message(record.message)
        except DisabledError:
            pass
        except Exception as ex:
            log.warn('Unable to store exception message: %s', ex, exc_info=True)

ERROR_STORAGE_HANDLER = ErrorStorage()
