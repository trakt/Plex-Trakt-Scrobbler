from plugin.sync.core.task.configuration.options import OPTIONS


class SyncConfiguration(object):
    options = OPTIONS

    def __init__(self, task):
        self.task = task

        self._options = {}

    def load(self, account):
        # Load options from database
        for prop in self.options:
            self._options[prop.key] = prop.get(account)

    def __getitem__(self, key):
        return self._options[key].value
