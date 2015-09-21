from plugin.sync.modes.core.base import PullListsMode

import logging
import urllib

log = logging.getLogger(__name__)


class Lists(PullListsMode):
    def process(self, data, p_playlists, p_sections_map, t_list):
        log.debug('Processing list: %r', t_list)

        # Create/retrieve plex list
        p_playlist = self.get_playlist(
            p_playlists,
            uri='trakt://list/%s/%s' % (self.current.account.id, t_list.id),
            title=t_list.name
        )

        if not p_playlist:
            return

        # Retrieve trakt list items from cache
        t_items = self.trakt[(data, t_list.id)]

        if not t_items:
            log.warn('Unable to retrieve list items for: %r', t_list)
            return

        # Map trakt list items into plex playlist
        self.process_items(data, p_sections_map, p_playlist, t_items)

    def process_items(self, data, p_sections_map, p_playlist, t_items):
        # Retrieve current playlist items
        p_playlist_items = dict([
            (int(item.rating_key), item)
            for item in p_playlist.items()
        ])

        # Iterate over items in trakt list
        for key, t_item in t_items.items():
            # Get `SyncMedia` for `t_item`
            media = self.get_media(t_item)

            if media is None:
                continue

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            if pk is None:
                log.info('Unable to map %r to a primary key', key)
                pk = key

            # Retrieve plex items that match `pk`
            p_keys = self.current.map.by_guid(pk)

            if not p_keys:
                log.info('Unable to find item that matches guid: %r', pk)
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

                playlist=p_playlist,
                playlist_items=p_playlist_items,

                t_item=t_item,

                p_keys=p_keys,
                uri=uri
            )
