from trakt_sync.differ.core.base import Differ
from trakt_sync.differ.core.result import Result
from trakt_sync.differ.handlers import List


class ListDiffer(Differ):
    def __init__(self):
        self.handlers = [
            h(self) for h in [
                List
            ]
        ]

    def run(self, base, current):
        b = set(base.keys())
        c = set(current.keys())

        result = ListResult()

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


class ListResult(Result):
    def __init__(self):
        super(ListResult, self).__init__()

        self.metrics = ListMetrics()


class ListMetrics(object):
    def __init__(self):
        self.movies = {}
