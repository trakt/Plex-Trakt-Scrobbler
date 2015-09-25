from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.modes.pull.lists.base import Lists

import elapsed
import logging
import trakt.objects

log = logging.getLogger(__name__)

MEDIA = [
    SyncMedia.Movies,
    SyncMedia.Shows,
    SyncMedia.Seasons,
    SyncMedia.Episodes
]


class Watchlist(Lists):
    mode = SyncMode.Pull

    @elapsed.clock
    def run(self):
        # Check if data is enabled
        if not self.is_data_enabled(SyncData.ListPersonal):
            log.debug('Personal list syncing has not been enabled')
            return

        # Retrieve plex sections
        p_sections, p_sections_map = self.sections()

        # Retrieve playlist
        p_playlists = dict(self.get_playlists())

        p_playlist = self.get_playlist(
            p_playlists,
            uri='trakt://watchlist/%s' % self.current.account.id,
            title='Watchlist'
        )

        if not p_playlist:
            return

        # Retrieve items from watchlist collections
        t_list_items = self.get_items(p_sections_map, p_playlist)

        # Update (add/remove) list items
        self.process_update(
            SyncData.Watchlist, p_playlist, p_sections_map,
            t_list_items=t_list_items
        )

    def get_items(self, p_sections_map, p_playlist):
        for media in MEDIA:
            # Retrieve trakt watchlist items from cache
            t_items = self.trakt[(media, SyncData.Watchlist)]

            if t_items is None:
                log.warn('Unable to retrieve items for %r watchlist', media)
                continue

            for item in t_items.itervalues():
                for t_item in self.expand_items(media, item):
                    yield t_item

    @staticmethod
    def expand_items(media, item):
        if media in [SyncMedia.Movies, SyncMedia.Shows]:
            yield item
        elif media == SyncMedia.Seasons:
            # Yield each season in show
            for t_season in item.seasons.itervalues():
                yield t_season
        elif media == SyncMedia.Episodes:
            # Iterate over each season in show
            for t_season in item.seasons.itervalues():
                # Yield each episode in season
                for t_episode in t_season.episodes.itervalues():
                    yield t_episode

    def create_playlist(self, uri, name):
        # Check if playlist creation is enabled
        if self.configuration['sync.lists.watchlist.playlists'] is False:
            log.info('No playlist found named %r ("Create playlist in plex" not enabled)', name)
            return None

        # Create playlist
        return super(Watchlist, self).create_playlist(uri, name)
