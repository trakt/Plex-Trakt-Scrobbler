class SyncBase(object):
    title = "Unknown"

    def run(self):
        raise NotImplementedError()

    @staticmethod
    def update_progress(current, start=0, end=100):
        raise ReferenceError()

    @staticmethod
    def is_stopping():
        raise ReferenceError()
