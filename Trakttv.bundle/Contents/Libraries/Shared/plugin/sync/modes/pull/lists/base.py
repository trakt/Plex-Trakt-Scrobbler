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
        t_items = self.trakt[(data, t_list.id)]

        if not t_items:
            log.warn('Unable to retrieve list items for: %r', t_list)
            return

        # Construct playlist mapper
        mapper = PlaylistMapper(self.current, p_sections_map)

        # Parse plex playlist items
        mapper.plex.load(p_playlist)

        # Parse trakt list items
        mapper.trakt.load(t_list, t_items.itervalues())

        # Match playlist items and expand shows/seasons
        t_items, p_items = mapper.match()

        log.info(
            'Mapper Result (%d items)\nt_items:\n%s\n\np_items:\n%s',
            len(t_items) + len(p_items),
            '\n'.join(self.format_items(t_items)),
            '\n'.join(self.format_items(p_items))
        )

        # Iterate over matched trakt items
        for key, index, (p_index, p_item), (t_index, t_item) in t_items:
            # Get `SyncMedia` for `t_item`
            media = self.get_media(t_item)

            if media is None:
                log.warn('Unable to identify media of "t_item" (p_item: %r, t_item: %r)', p_item, t_item)
                continue

            # Execute handler
            self.execute_handlers(
                media, data,

                p_sections_map=p_sections_map,
                p_playlist=p_playlist,

                key=key,

                p_item=p_item,
                t_item=t_item
            )

    @staticmethod
    def format_items(items):
        for key, index, (p_index, p_item), (t_index, t_item) in items:
            # Build key
            key = list(key)
            key[0] = '/'.join(key[0])

            key = '/'.join([str(x) for x in key])

            # Build indices
            if p_index is None:
                p_index = '---'

            if t_index is None:
                t_index = '---'

            yield '%s[%-16s](%3s) - %68s <[%3s] - [%3s]> %r' % (
                ' ' * 4,
                key, index,
                p_item, p_index,
                t_index, t_item
            )
