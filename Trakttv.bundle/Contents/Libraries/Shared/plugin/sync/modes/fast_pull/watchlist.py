from plugin.sync.core.enums import SyncData, SyncMode
from plugin.sync.modes.core.base import Mode

from plex import Plex
from trakt_sync.cache.main import Cache
import elapsed
import logging
import urllib

log = logging.getLogger(__name__)


class Watchlist(Mode):
    mode = SyncMode.FastPull

    def find_watchlist(self):
        # Try find existing playlist
        container = Plex['playlists'].all(playlist_type='video')

        if not container:
            return None

        for playlist in container:
            if not playlist or not playlist.title:
                continue

            if playlist.title.lower() == 'watchlist':
                return playlist

        # Create new playlist
        log.debug('Creating new watchlist for account %r', self.current.account.id)

        return Plex['playlists'].create(
            type='video',
            title='Watchlist',
            uri='trakt://watchlist/%s' % self.current.account.id
        )

    @elapsed.clock
    def run(self):
        # Retrieve sections
        p_sections, p_sections_map = self.sections()

        # Retrieve playlist
        playlist = self.find_watchlist()

        playlist_items = dict([
            (int(item.rating_key), item)
            for item in playlist.items()
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

            for action, items in result.changes[data_name].items():
                for guid in items:
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

                        playlist=playlist,
                        playlist_items=playlist_items,

                        p_keys=p_keys,
                        uri=uri
                    )
