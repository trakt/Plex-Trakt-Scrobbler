import logging


class Core(object):
    def __init__(self, code_path):
        self._code_path = code_path

    @property
    def code_path(self):
        return self._code_path


class Logger(object):
    def __init__(self):
        self._logger = logging.getLogger()

    def Debug(self, *args, **kwargs):
        self._logger.debug(*args, **kwargs)

    def Info(self, *args, **kwargs):
        self._logger.info(*args, **kwargs)

    def Warn(self, *args, **kwargs):
        self._logger.warn(*args, **kwargs)

    def Warning(self, *args, **kwargs):
        self._logger.warning(*args, **kwargs)

    def Error(self, *args, **kwargs):
        self._logger.error(*args, **kwargs)

    def Fatal(self, *args, **kwargs):
        self._logger.fatal(*args, **kwargs)
