class SyncTask(object):
    def __init__(self, handler, kwargs):
        self.handler = handler
        self.kwargs = kwargs

        self.status = SyncStatus()

        self.start_time = None
        self.end_time = None

        self.stopping = False


class SyncStatus(object):
    def __init__(self):
        self.progress = None
        self.seconds_remaining = None

        self.per_perc = None
        self.plots = []

        self.last_update = None
