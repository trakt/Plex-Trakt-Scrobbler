class SyncModule(object):
    __data__ = None

    def __init__(self, main):
        self.__main = main

    def run_pull(self):
        raise NotImplementedError

    def run_push(self):
        raise NotImplementedError

    def run_full(self):
        # TODO default implementation to run `pull()` then `push()`
        raise NotImplementedError
