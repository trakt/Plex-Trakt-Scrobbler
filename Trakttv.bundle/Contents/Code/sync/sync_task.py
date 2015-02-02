import uuid


class SyncTask(object):
    def __init__(self, key, kwargs):
        self.key = key
        self.kwargs = kwargs

        self.sid = uuid.uuid4()
        self.statistics = SyncTaskStatistics()

        self.start_time = None
        self.end_time = None
        self.success = None

        self.stopping = False


class SyncTaskStatistics(object):
    def __init__(self):
        self.message = None

        self.progress = None
        self.seconds_remaining = None

        self.per_perc = None
        self.plots = []

        self.last_update = None
