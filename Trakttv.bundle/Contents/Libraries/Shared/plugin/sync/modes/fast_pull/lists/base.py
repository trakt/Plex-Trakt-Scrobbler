from plugin.sync.core.enums import SyncMedia
from plugin.sync.core.playlist.mapper import PlaylistMapper
from plugin.sync.modes.core.base import PullListsMode

from trakt_sync.cache.main import Cache
import logging

log = logging.getLogger(__name__)


class Lists(PullListsMode):
    def process(self, data, p_playlists, p_sections_map):
        # Iterate over trakt list changes
        for key, result in self.get_changed_lists(data):
            if 'lists' not in result.changes:
                log.warn('Unable to find "lists" key in changes: %r', result.changes)
                continue

            for action, t_items in result.changes['lists'].items():
                for t_list_id, t_item in t_items.items():
                    # Try retrieve trakt list
                    t_list = self.trakt[key].get(t_list_id)

                    # Execute handlers for list
                    self.execute_handlers(
                        self.mode, SyncMedia.Lists, data,
                        action=action,

                        p_playlists=p_playlists,

                        key=t_list_id,

                        t_list=t_list
                    )

                    if action == 'removed':
                        # No changes to list items required
                        continue

                    if not t_list:
                        # List was removed
                        continue

                    # Process list items
                    self.process_list(action, data, p_playlists, p_sections_map, t_list)

    def process_list(self, action, data, p_playlists, p_sections_map, t_list):
        log.debug('Processing list: %r', t_list)

        # Create/retrieve plex list
        p_playlist = self.get_playlist(
            p_playlists,
            uri='trakt://list/%s/%s' % (self.current.account.id, t_list.id),
            title=t_list.name
        )

        if not p_playlist:
            log.warn('Unable to create/retrieve playlist with name: %r', t_list.name)
            return

        # Retrieve trakt list items from cache
        t_list_items = self.trakt[(SyncMedia.Lists, data, t_list.id)]

        if t_list_items is None:
            log.warn('Unable to retrieve list items for: %r', t_list)
            return

        # Update (add/remove) list items
        if action == 'added':
            self.update_full(data, p_playlist, p_sections_map, t_list, t_list_items.itervalues())
        elif action == 'changed':
            self.update_changed(data, p_playlist, p_sections_map, t_list, t_list_items.itervalues())
        else:
            log.warn('Unsupported action for process(): %r', action)
            return

        # TODO Sort list items
        # self.process_sort(data, p_playlist, p_sections_map, t_list, t_list_items.itervalues())

    def update_changed(self, data, p_playlist, p_sections_map, t_list=None, t_list_items=None):
        # Retrieve changed items
        t_changes = self.get_changed_items(data)

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
            '\n'.join(self.format_mapper_result(m_trakt)),
            '\n'.join(self.format_mapper_result(m_plex))
        )

        log.debug(
            'Update - Changes (%d keys)\n%s',
            len(t_changes),
            '\n'.join(self.format_changes(t_changes)),
        )

        # Iterate over matched trakt items
        for key, index, (p_index, p_items), (t_index, t_items) in m_trakt:
            # Expand shows/seasons into episodes
            for p_item, t_item in self.expand(p_items, t_items):
                if not t_item:
                    continue

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
                    self.mode, media, data,

                    action=actions[0],

                    p_sections_map=p_sections_map,
                    p_playlist=p_playlist,

                    key=key,

                    p_item=p_item,
                    t_item=t_item
                )

    def update_full(self, data, p_playlist, p_sections_map, t_list=None, t_list_items=None):
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

    def get_changed_lists(self, data, extra=None):
        for key, result in self.trakt.changes:
            m, d = key[0:2]

            if len(key) > 2:
                e = key[2:]
            else:
                e = None

            if m != SyncMedia.Lists:
                continue

            if d != data:
                continue

            if extra is True and e is None:
                continue
            elif e != extra:
                continue

            yield key, result

    def get_changed_items(self, data):
        changes = {}

        for key, result in self.trakt.changes:
            m, d = key[0:2]

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
