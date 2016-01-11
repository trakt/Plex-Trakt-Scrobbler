from trakt_sync.differ.core.base import Differ
from trakt_sync.differ.core.result import Result
from trakt_sync.differ.handlers import Lists


class ListsDiffer(Differ):
    def __init__(self):
        self.handlers = [
            h(self) for h in [
                Lists
            ]
        ]

    def run(self, base, current):
        b = set(base.keys())
        c = set(current.keys())

        result = ListsResult(self)

        for key in c - b:
            actions = self.process_added(current[key])

            self.store_actions(result, actions)

        for key in b - c:
            actions = self.process_removed(base[key])

            self.store_actions(result, actions)

        for key in b & c:
            actions = self.process_common(base[key], current[key])

            self.store_actions(result, actions)

        return result


class ListsResult(Result):
    def __init__(self, differ):
        super(ListsResult, self).__init__(differ)

        self.metrics = ListsMetrics()


class ListsMetrics(object):
    def __init__(self):
        self.movies = {}
