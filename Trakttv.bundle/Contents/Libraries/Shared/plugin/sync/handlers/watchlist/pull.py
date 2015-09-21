from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, MediaHandler, bind

import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, **kwargs):
        return kwargs

    def get_action(self, p_items, t_item):
        # Convert to list
        p_items = list(p_items)

        if not p_items and t_item:
            return 'added'

        if p_items and not t_item:
            return 'removed'

        return None

    def fast_pull(self, action, playlist_items, p_keys, *args, **kwargs):
        if not action:
            # No action provided
            return

        # Try find matching plex items
        p_items = self.match(playlist_items, p_keys)

        # Execute action
        self.execute_action(
            action,

            p_items=p_items,
            *args, **kwargs
        )

    def pull(self, playlist_items, p_keys, t_item, *args, **kwargs):
        # Try find matching plex items
        p_items = self.match(playlist_items, p_keys)

        # Determine performed action
        action = self.get_action(p_items, t_item)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(
            action,

            p_items=p_items,
            t_item=t_item,
            **kwargs
        )

    #
    # Action handlers
    #

    @bind('added')
    def on_added(self, playlist, p_items, t_item, uri):
        log.debug('%s.on_added(uri: %r)', self.media, uri)

        # Check if item has already been added
        p_items = list(p_items)

        if len(p_items) > 0:
            log.debug('Item %r already in watchlist', uri)
            return

        # Add item to playlist
        playlist.add(uri)

    @bind('removed', [SyncMode.Full, SyncMode.FastPull])
    def on_removed(self, playlist, p_items, t_item, uri):
        log.debug('%s.on_removed(uri: %r)', self.media, uri)

        # Find matching items in watchlist
        for p_item in p_items:
            # Remove item from playlist
            playlist.remove(p_item.playlist_item_id)

    #
    # Helpers
    #

    @staticmethod
    def match(playlist_items, p_keys):
        for _, p_item_key in p_keys:
            p_item = playlist_items.get(p_item_key)

            if p_item is not None:
                yield p_item

    @classmethod
    def has_key(cls, playlist_items, p_keys):
        for p_item in cls.match(playlist_items, p_keys):
            # Item found
            return True

        # No items found matching `p_keys`
        return False


class Movies(Base):
    media = SyncMedia.Movies


class Shows(Base):
    media = SyncMedia.Shows


class Seasons(Base):
    media = SyncMedia.Seasons


class Episodes(Base):
    media = SyncMedia.Episodes


class Pull(DataHandler):
    data = SyncData.Watchlist
    mode = [SyncMode.FastPull, SyncMode.Pull]

    children = [
        Movies,
        Shows,
        Seasons,
        Episodes
    ]
