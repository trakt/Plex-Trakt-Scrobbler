from plugin.sync.core.enums import SyncData, SyncMode
from plugin.sync.modes.fast_pull.lists.base import Lists

from plex import Plex
from trakt_sync.cache.main import Cache
import elapsed
import logging
import urllib

log = logging.getLogger(__name__)


class Watchlist(Lists):
    mode = SyncMode.FastPull

    @elapsed.clock
    def run(self):
        # Check if data is enabled
        if not self.is_data_enabled(SyncData.Watchlist):
            log.debug('Watchlist syncing has not been enabled')
            return

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

        p_playlist_items = dict([
            (int(item.rating_key), item)
            for item in p_playlist.items()
        ])

        # Iterate over changed data
        for (media, data), result in self.trakt.changes:
            if data != SyncData.Watchlist:
                # Ignore non-watchlist data
                continue

            if not self.is_data_enabled(data):
                # Data type has been disabled
                continue

            data_name = Cache.Data.get(data)

            if data_name not in result.changes:
                # No changes for collection
                continue

            for action, t_items in result.changes[data_name].items():
                for guid, t_item in t_items.items():
                    p_keys = self.current.map.by_guid(guid)

                    if not p_keys:
                        # Item not found in plex
                        continue

                    # Convert to list (for indexing)
                    p_keys = list(p_keys)

                    # Use first match found in plex
                    p_section_key, p_item_key = p_keys[0]

                    # Retrieve section UUID
                    p_section_uuid = p_sections_map.get(p_section_key)

                    # Build URI
                    uri = 'library://%s/item/%s' % (
                        p_section_uuid,
                        urllib.quote_plus('/library/metadata/%s' % p_item_key)
                    )

                    # Execute handler
                    self.execute_handlers(
                        media, data,
                        action=action,

                        playlist=p_playlist,
                        playlist_items=p_playlist_items,

                        t_item=t_item,

                        p_keys=p_keys,
                        uri=uri
                    )

    def create_playlist(self, uri, name):
        # Check if playlist creation is enabled
        if self.configuration['sync.lists.watchlist.playlists'] is False:
            log.info('No playlist found named %r ("Create playlist in plex" not enabled)', name)
            return None

        # Create playlist
        return super(Watchlist, self).create_playlist(uri, name)
