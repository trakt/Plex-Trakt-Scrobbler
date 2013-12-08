from threading import Thread


class SyncBase(object):
    def run(self):
        raise NotImplementedError()
