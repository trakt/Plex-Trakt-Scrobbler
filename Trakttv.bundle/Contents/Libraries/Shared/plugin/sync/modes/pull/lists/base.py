from plugin.sync.core.enums import SyncMedia
from plugin.sync.core.playlist.mapper import PlaylistMapper
from plugin.sync.modes.core.base import PullListsMode

import logging

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
        t_list_items = self.trakt[(SyncMedia.Lists, data, t_list.id)]

        if t_list_items is None:
            log.warn('Unable to retrieve list items for: %r', t_list)
            return

        # Update (add/remove) list items
        self.process_update(data, p_playlist, p_sections_map, t_list, t_list_items.itervalues())

        # Sort list items
        self.process_sort(data, p_playlist, p_sections_map, t_list, t_list_items.itervalues())

    def process_update(self, data, p_playlist, p_sections_map, t_list=None, t_list_items=None):
        # Construct playlist mapper
        mapper = PlaylistMapper(self.current, p_sections_map)

        # Parse plex playlist items
        mapper.plex.load(p_playlist)

        # Parse trakt list items
        mapper.trakt.load(t_list, t_list_items)

        # Match playlist items and expand shows/seasons
        m_trakt, m_plex = mapper.match()

        log.debug(
            'Update - Mapper Result (%d items)\nt_items:\n%s\n\np_items:\n%s',
            len(m_trakt) + len(m_plex),
            '\n'.join(self.format_mapper_result(m_trakt)),
            '\n'.join(self.format_mapper_result(m_plex))
        )

        # Iterate over matched trakt items
        for key, index, (p_index, p_items), (t_index, t_items) in m_trakt:
            # Expand shows/seasons into episodes
            for p_item, t_item in self.expand(p_items, t_items):
                if not t_item:
                    continue

                # Get `SyncMedia` for `t_item`
                media = self.get_media(t_item)

                if media is None:
                    log.warn('Unable to identify media of "t_item" (p_item: %r, t_item: %r)', p_item, t_item)
                    continue

                # Execute handler
                self.execute_handlers(
                    self.mode, media, data,

                    p_sections_map=p_sections_map,
                    p_playlist=p_playlist,

                    key=key,

                    p_item=p_item,
                    t_item=t_item
                )

    def process_sort(self, data, p_playlist, p_sections_map, t_list, t_list_items):
        # Construct playlist mapper
        mapper = PlaylistMapper(self.current, p_sections_map)

        # Parse plex playlist items
        mapper.plex.load(p_playlist)

        # Parse trakt list items
        mapper.trakt.load(t_list, t_list_items)

        # Match playlist items and expand shows/seasons
        m_trakt, m_plex = mapper.match()

        log.debug(
            'Sort - Mapper Result (%d items)\nt_items:\n%s\n\np_items:\n%s',
            len(m_trakt) + len(m_plex),
            '\n'.join(self.format_mapper_result(m_trakt)),
            '\n'.join(self.format_mapper_result(m_plex))
        )

        # Build a list of plex items (sorted by `p_index`)
        p_playlist_items = []

        for item in mapper.plex.items.itervalues():
            p_playlist_items.append(item)

        p_playlist_items = [
            i[1]
            for i in sorted(p_playlist_items, key=lambda i: i[0])
        ]

        # Iterate over trakt items, re-order plex items
        t_index = 0

        for key, _, (_, p_items), (_, t_items) in m_trakt:
            # Expand shows/seasons into episodes
            for p_item, t_item in self.expand(p_items, t_items):
                if not p_item:
                    continue

                if p_item not in p_playlist_items:
                    log.info('Unable to find %r in "p_playlist_items"', p_item)
                    t_index += 1
                    continue

                p_index = p_playlist_items.index(p_item)

                if p_index == t_index:
                    t_index += 1
                    continue

                p_after = p_playlist_items[t_index - 1] if t_index > 0 else None

                log.info('[%2d:%2d] p_item: %r, t_item: %r (move after: %r)',
                    p_index, t_index,
                    p_item, t_item,
                    p_after
                )

                # Move item in plex playlist
                p_playlist.move(
                    p_item.playlist_item_id,
                    p_after.playlist_item_id if p_after else None
                )

                # Remove item from current position
                if t_index > p_index:
                    p_playlist_items[p_index] = None
                else:
                    p_playlist_items.pop(p_index)

                # Insert at new position
                if p_playlist_items[t_index] is None:
                    p_playlist_items[t_index] = p_item
                else:
                    p_playlist_items.insert(t_index, p_item)

                t_index += 1
