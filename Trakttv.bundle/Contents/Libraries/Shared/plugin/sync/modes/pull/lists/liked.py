from plugin.sync.core.enums import SyncData, SyncMode
from plugin.sync.modes.pull.lists.base import Lists

import elapsed
import logging

log = logging.getLogger(__name__)


class LikedLists(Lists):
    mode = SyncMode.Pull

    @elapsed.clock
    def run(self):
        # Check if data is enabled
        if not self.is_data_enabled(SyncData.ListLiked):
            log.debug('Liked list syncing is not enabled')
            return

        # Retrieve plex sections
        p_sections, p_sections_map = self.sections()

        # Retrieve plex playlists
        p_playlists = dict(self.get_playlists())

        # Retrieve trakt lists
        t_lists = self.trakt[(SyncData.ListLiked,)]

        if t_lists is None:
            log.warn('Unable to retrieve liked lists')
            return

        # Process trakt lists
        for _, t_list in t_lists.items():
            self.process(SyncData.ListLiked, p_playlists, p_sections_map, t_list)
