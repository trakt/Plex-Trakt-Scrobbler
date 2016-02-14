from trakt_sync.differ.core.helpers import dict_path


class Result(object):
    def __init__(self, differ):
        self.changes = {}

        self._differ = differ

    def add(self, current):
        for handler in self._differ.handlers:
            items = dict_path(self.changes, (
                handler.name, 'added'
            ))

            for key, item in current.items():
                items[key] = handler.properties(item)
