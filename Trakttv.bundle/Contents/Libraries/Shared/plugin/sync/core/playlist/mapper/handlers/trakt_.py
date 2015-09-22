from plugin.sync.core.playlist.mapper.handlers.base import PlaylistHandler

from trakt.objects import Movie, Show, Season, Episode


class TraktPlaylistHandler(PlaylistHandler):
    def __init__(self, task):
        super(TraktPlaylistHandler, self).__init__(task)

        self.playlist = None
        self.items = None

    def load(self, playlist, items=None):
        if items is None:
            # Fetch playlist items
            items = playlist.items()

        self.playlist = playlist

        self.items = {}
        self.table = {}

        # Parse items into the `items` and `table` attribute
        self.parse(items)

    def keys_ordered(self):
        return [
            key for key, _ in sorted(
                self.items.items(),
                key=lambda (k, i): i.index
            )
        ]

    #
    # Item parser
    #

    def build_key(self, item):
        i_type = type(item)

        if i_type is Movie:
            return [item.pk]

        if i_type is Show:
            return [item.pk]

        if i_type is Season:
            return [item.show.pk, item.pk]

        if i_type is Episode:
            return [item.show.pk] + list(item.pk)

        raise ValueError('Unknown item type: %r' % i_type)

    def parse(self, items):
        for item in items:
            keys = self.build_key(item)

            if keys is None:
                continue

            # Update `items`
            self.items[tuple(keys)] = item

            # Update `table`
            self.path_set(self.table, keys, item)
