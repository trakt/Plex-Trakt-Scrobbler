from trakt.objects import Show
from trakt.objects import Movie
from trakt_sync.differ.core.helpers import dict_path

KEY_AGENTS = [
    'imdb',
    'tmdb',
    'tvdb',
    'tvrage'
]


class Differ(object):
    handlers = None

    def run(self, base, current):
        raise NotImplementedError

    def process_added(self, current, handlers=None):
        for h in self.handlers:
            if handlers is not None and h.name not in handlers:
                continue

            for action in h.on_added(current):
                yield action

    def process_removed(self, base, handlers=None):
        for h in self.handlers:
            if handlers is not None and h.name not in handlers:
                continue

            for action in h.on_removed(base):
                yield action

    def process_common(self, base, current, handlers=None):
        for h in self.handlers:
            if handlers is not None and h.name not in handlers:
                continue

            for action in h.on_common(base, current):
                yield action

    @staticmethod
    def store_action(changes, keys, collection, action, properties=None):
        items = dict_path(changes, (
            collection, action
        ))

        for key in keys:
            items[key] = properties

    @classmethod
    def store_actions(cls, changes, actions):
        for action in actions:
            cls.store_action(changes, *action)

    @classmethod
    def store_child(cls, changes, key, media, data):
        if not data:
            return

        if media not in changes:
            changes[media] = {}

        changes[media][key] = data

    @staticmethod
    def item_keys(item):
        if type(item) not in [Show, Movie]:
            yield item.pk
            return

        for agent, sid in item.keys:
            if agent not in KEY_AGENTS:
                continue

            yield agent, sid
