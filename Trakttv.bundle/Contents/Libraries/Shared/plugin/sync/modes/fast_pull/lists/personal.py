from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.modes.fast_pull.lists.base import Lists

import elapsed
import logging

log = logging.getLogger(__name__)


class PersonalLists(Lists):
    data = [SyncData.Personal]
    mode = SyncMode.FastPull

    @elapsed.clock
    def run(self):
        # Retrieve sections
        p_sections, p_sections_map = self.sections()

        # Retrieve playlists
        p_playlists = dict(self.get_playlists())

        # Process list changes
        self.process(SyncData.Personal, p_playlists, p_sections_map)

    def create_playlist(self, uri, name):
        # Check if playlist creation is enabled
        if self.configuration['sync.lists.personal.playlists'] is False:
            log.info('No playlist found named %r ("Create playlist in plex" not enabled)', name)
            return None

        # Create playlist
        return super(PersonalLists, self).create_playlist(uri, name)
