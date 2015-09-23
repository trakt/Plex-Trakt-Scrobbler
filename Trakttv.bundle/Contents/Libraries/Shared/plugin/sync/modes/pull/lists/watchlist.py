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

        # TODO update to use `PlaylistMapper`

    def create_playlist(self, uri, name):
        # Check if playlist creation is enabled
        if self.configuration['sync.lists.watchlist.playlists'] is False:
            log.info('No playlist found named %r ("Create playlist in plex" not enabled)', name)
            return None

        # Create playlist
        return super(Watchlist, self).create_playlist(uri, name)
