from trakt_sync.differ.core.base import Differ
from trakt_sync.differ.core.helpers import dict_path
from trakt_sync.differ.core.result import Result
from trakt_sync.differ.handlers import Collection, Playback, Ratings, Watched


class MovieDiffer(Differ):
    def __init__(self):
        self.handlers = [
            h(self) for h in [
                Collection,
                Playback,
                Ratings,
                Watched
            ]
        ]

    def run(self, base, current, handlers=None):
        b = set(base.keys())
        c = set(current.keys())

        result = MovieResult()

        for key in c - b:
            actions = self.process_added(current[key], handlers=handlers)

            self.store_actions(result, actions)

        for key in b - c:
            actions = self.process_removed(base[key], handlers=handlers)

            self.store_actions(result, actions)

        for key in b & c:
            actions = self.process_common(base[key], current[key], handlers=handlers)

            self.store_actions(result, actions)

        return result

    @staticmethod
    def store_action(result, keys, collection, action, properties=None):
        Differ.store_action(result, keys, collection, action, properties)

        # Update movie metrics
        Differ.increment_metric(result.metrics.movies, collection, action)


class MovieResult(Result):
    def __init__(self):
        super(MovieResult, self).__init__()

        self.metrics = MovieMetrics()


class MovieMetrics(object):
    def __init__(self):
        self.movies = {}
