from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.modes.fast_pull.lists.base import Lists

import elapsed
import logging

log = logging.getLogger(__name__)


class Watchlist(Lists):
    data = [SyncData.Watchlist]
    mode = SyncMode.FastPull

    @elapsed.clock
    def run(self):
        # Retrieve sections
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
        t_list_items = self.get_items(SyncData.Watchlist, [
            SyncMedia.Movies,
            SyncMedia.Shows,
            SyncMedia.Seasons,
            SyncMedia.Episodes
        ])

        # Update (add/remove) list items
        self.update_changed(
            SyncData.Watchlist, p_playlist, p_sections_map,
            t_list_items=t_list_items
        )

    def create_playlist(self, uri, name):
        # Check if playlist creation is enabled
        if self.configuration['sync.lists.watchlist.playlists'] is False:
            log.info('No playlist found named %r ("Create playlist in plex" not enabled)', name)
            return None

        # Create playlist
        return super(Watchlist, self).create_playlist(uri, name)
