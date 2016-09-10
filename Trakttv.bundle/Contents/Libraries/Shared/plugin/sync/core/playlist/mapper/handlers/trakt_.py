from plugin.sync.core.playlist.mapper.handlers.base import PlaylistHandler

from trakt.objects import Movie, Show, Season, Episode
import logging

log = logging.getLogger(__name__)


class TraktPlaylistHandler(PlaylistHandler):
    def __init__(self, task):
        super(TraktPlaylistHandler, self).__init__(task)

        self.playlist = None
        self.items = None

    def load(self, playlist=None, items=None):
        if items is None:
            if playlist is None:
                raise ValueError('Either the "playlist" or "items" parameter is required')

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

        log.debug('Ignoring unsupported list item: %r', item)
        return None

    def parse(self, items):
        for item in items:
            keys = self.build_key(item)

            if keys is None:
                continue

            # Update `items`
            self.items[tuple(keys)] = item

            # Update `table`
            if not self.path_set(self.table, keys, item):
                log.info('Unable to update table (keys: %r)', keys)
