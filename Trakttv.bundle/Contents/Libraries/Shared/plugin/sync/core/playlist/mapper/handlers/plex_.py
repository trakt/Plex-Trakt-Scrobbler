from plugin.sync.core.playlist.mapper.handlers.base import PlaylistHandler

from plex.objects.library.metadata.movie import Movie
from plex.objects.library.metadata.show import Show
from plex.objects.library.metadata.season import Season
from plex.objects.library.metadata.episode import Episode
import logging

log = logging.getLogger(__name__)


class PlexPlaylistHandler(PlaylistHandler):
    def __init__(self, task):
        super(PlexPlaylistHandler, self).__init__(task)

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

    #
    # Item parser
    #

    def build_key(self, item):
        i_type = type(item)

        if hasattr(item, 'show'):
            root = item.show
        else:
            root = item

        # Retrieve guid for `item`
        guids = list(self.task.map.by_key(root.rating_key))

        if len(guids) < 1:
            log.warn('Unable to find any guids for item #%s', root.rating_key)
            return None

        if len(guids) > 1:
            log.warn('Multiple guids returned for %r', item)

        guid = guids[0]

        # Try map `guid` to a primary agent
        guid = self.task.state.trakt.table.get(guid, guid)

        # Build key for `item`
        if i_type in [Movie, Show]:
            return [guid]

        if i_type is Season:
            return [guid, item.index]

        if i_type is Episode:
            return [guid, item.season.index, item.index]

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
