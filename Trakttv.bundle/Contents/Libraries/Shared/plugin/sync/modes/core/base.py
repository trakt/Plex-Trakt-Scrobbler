class Mode(object):
    mode = None

    def __init__(self, main):
        self.__main = main

    @property
    def current(self):
        return self.__main.current

    @property
    def handlers(self):
        return self.__main.handlers

    def run(self):
        raise NotImplementedError
