from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.modes.pull.lists.base import Lists

import elapsed
import logging

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

        for media in MEDIA:
            # Retrieve trakt watchlist items from cache
            t_items = self.trakt[(media, SyncData.Watchlist)]

            if t_items is None:
                log.warn('Unable to retrieve items for %r watchlist', media)
                continue

            # Map trakt list items into plex playlist
            self.process_items(SyncData.Watchlist, p_sections_map, p_playlist, t_items)
