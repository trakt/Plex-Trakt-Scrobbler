from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, MediaHandler, bind

import logging
import urllib

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, **kwargs):
        return kwargs

    def get_action(self, p_index, p_item, t_index, t_item):
        if not p_item and t_item:
            return 'added'

        if p_item and not t_item:
            return 'removed'

        if p_index != t_index:
            return 'moved'

        return None

    def pull(self, key, p_item, t_item, p_index=None, t_index=None, *args, **kwargs):
        # Determine performed action
        action = self.get_action(p_index, p_item, t_index, t_item)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(
            action,

            key=key,

            p_item=p_item,
            t_item=t_item,
            **kwargs
        )

    #
    # Action handlers
    #

    @bind('added')
    def on_added(self, p_sections_map, p_playlist, key, p_item, t_item):
        # Find item in plex matching `t_item`
        p_key = self.match(*key)

        if p_key is None:
            log.debug('Unable to find item that matches item: %r', t_item)
            return

        log.debug('%s.on_added(p_key: %r)', self.media, p_key)

        # Build uri for plex item
        uri = self.build_uri(p_sections_map, *p_key)

        # Add item to playlist
        p_playlist.add(uri)

    #
    # Helpers
    #

    @staticmethod
    def build_uri(p_sections_map, p_section_key, p_item_key):
        # Retrieve section UUID
        p_section_uuid = p_sections_map.get(p_section_key)

        # Build URI
        return 'library://%s/item/%s' % (
            p_section_uuid,
            urllib.quote_plus('/library/metadata/%s' % p_item_key)
        )

    def match(self, key, *extra):
        # Try retrieve `pk` for `key`
        pk = self.current.state.trakt.table.get(key)

        if pk is None:
            log.debug('Unable to map %r to a primary key', key)
            pk = key

        # Retrieve plex items that match `pk`
        p_keys = self.current.map.by_guid(pk)

        if not p_keys:
            return None

        # Convert to list (for indexing)
        p_keys = list(p_keys)

        # Use first match found in plex
        return p_keys[0]


class Movies(Base):
    media = SyncMedia.Movies


class Shows(Base):
    media = SyncMedia.Shows


class Seasons(Base):
    media = SyncMedia.Seasons


class Episodes(Base):
    media = SyncMedia.Episodes


class Pull(DataHandler):
    data = [SyncData.ListLiked, SyncData.ListPersonal]
    mode = [SyncMode.FastPull, SyncMode.Pull]

    children = [
        Movies,
        Shows,
        Seasons,
        Episodes
    ]
