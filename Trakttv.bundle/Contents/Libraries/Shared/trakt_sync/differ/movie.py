from trakt_sync.differ.core.base import Differ
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

        changes = {}

        for key in c - b:
            actions = self.process_added(current[key], handlers=handlers)

            self.store_actions(changes, actions)

        for key in b - c:
            actions = self.process_removed(base[key], handlers=handlers)

            self.store_actions(changes, actions)

        for key in b & c:
            actions = self.process_common(base[key], current[key], handlers=handlers)

            self.store_actions(changes, actions)

        return changes
