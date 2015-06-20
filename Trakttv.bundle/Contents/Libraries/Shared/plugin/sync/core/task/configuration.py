from plugin.preferences import OPTIONS_BY_KEY


class SyncConfiguration(object):
    options = [
        'sync.collection.mode',
        'sync.collection.clean',

        'sync.ratings.mode',
        'sync.ratings.conflict',

        'sync.playback.mode',
        'sync.watched.mode'
    ]

    def __init__(self, task):
        self.task = task

        self._options = {}

    def load(self, account):
        # Load options from database
        for key in self.options:
            self._options[key] = OPTIONS_BY_KEY[key].get(account)

    def __getitem__(self, key):
        return self._options[key].value
