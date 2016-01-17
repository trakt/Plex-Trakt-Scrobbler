from plugin.sync.core.enums import SyncData, SyncMode, SyncMedia
from plugin.sync.modes.pull.lists.base import Lists

import elapsed
import logging

log = logging.getLogger(__name__)


class LikedLists(Lists):
    mode = SyncMode.Pull

    @elapsed.clock
    def run(self):
        # Check if data is enabled
        if not self.is_data_enabled(SyncData.Liked):
            log.debug('Liked list syncing is not enabled')
            return

        # Retrieve plex sections
        p_sections, p_sections_map = self.sections()

        # Retrieve plex playlists
        p_playlists = dict(self.get_playlists())

        # Retrieve trakt lists
        t_lists = self.trakt[(SyncMedia.Lists, SyncData.Liked)]

        if t_lists is None:
            log.warn('Unable to retrieve liked lists')
            return

        # Process trakt lists
        for _, t_list in t_lists.items():
            self.process(SyncData.Liked, p_playlists, p_sections_map, t_list)

    def create_playlist(self, uri, name):
        # Check if playlist creation is enabled
        if self.configuration['sync.lists.liked.playlists'] is False:
            log.info('No playlist found named %r ("Create playlists in plex" not enabled)', name)
            return None

        # Create playlist
        return super(LikedLists, self).create_playlist(uri, name)
