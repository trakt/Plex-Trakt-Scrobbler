from plugin.sync.core.playlist.mapper import PlaylistMapper
from plugin.sync.modes.core.base import PullListsMode

from trakt_sync.cache.main import Cache
import logging

log = logging.getLogger(__name__)


class Lists(PullListsMode):
    def process(self, data, p_playlists, p_sections_map, t_list):
        pass

    def process_update(self, data, p_playlist, p_sections_map, t_list=None, t_list_items=None):
        # Retrieve changed items
        t_changes = self.get_changes(data)

        if not t_changes:
            log.debug('No changes detected in %r collection', data)
            return

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
            '\n'.join(self.format_items(m_trakt)),
            '\n'.join(self.format_items(m_plex))
        )

        log.debug(
            'Update - Changes (%d keys)\n%s',
            len(t_changes),
            '\n'.join([
                '    [%s] actions: %r' % (
                    key, actions
                )
                for key, actions in t_changes.items()
            ])
        )

        # Iterate over matched trakt items
        for key, index, (p_index, p_items), (t_index, t_items) in m_trakt:
            # Expand shows/seasons into episodes
            for p_item, t_item in self.expand(p_items, t_items):
                if len(key) < 1:
                    log.warn('Invalid "key" format: %r', key)
                    continue

                actions = list(t_changes.get(key[0], []))

                if not actions:
                    continue

                if len(actions) > 1:
                    log.warn('Multiple actions returned for %r: %r', key[0], actions)
                    continue

                # Get `SyncMedia` for `t_item`
                media = self.get_media(t_item)

                if media is None:
                    log.warn('Unable to identify media of "t_item" (p_item: %r, t_item: %r)', p_item, t_item)
                    continue

                # Execute handler
                self.execute_handlers(
                    media, data,

                    action=actions[0],

                    p_sections_map=p_sections_map,
                    p_playlist=p_playlist,

                    key=key,

                    p_item=p_item,
                    t_item=t_item
                )

    def get_changes(self, data):
        changes = {}

        for (m, d), result in self.trakt.changes:
            if d != data:
                # Ignore non-watchlist data
                continue

            if not self.is_data_enabled(d):
                # Data type has been disabled
                continue

            data_name = Cache.Data.get(d)

            if data_name not in result.changes:
                # No changes for collection
                continue

            for action, t_items in result.changes[data_name].items():
                for guid, t_item in t_items.items():
                    if guid not in changes:
                        changes[guid] = set()

                    changes[guid].add(action)

        return changes
