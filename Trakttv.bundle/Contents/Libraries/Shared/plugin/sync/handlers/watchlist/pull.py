from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, MediaHandler, bind

import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, **kwargs):
        return kwargs

    def fast_pull(self, action, *args, **kwargs):
        if not action:
            # No action provided
            return

        # Execute action
        self.execute_action(action, *args, **kwargs)

    #
    # Action handlers
    #

    @bind('added')
    def on_added(self, playlist, playlist_items, p_keys, uri):
        log.debug('%s.on_added(uri: %r)', self.media, uri)

        # Check if item has already been added
        if self.has_key(playlist_items, p_keys):
            log.debug('Item %r already in watchlist', uri)
            return

        # Add item to playlist
        playlist.add(uri)

    @bind('removed', [SyncMode.Full, SyncMode.FastPull])
    def on_removed(self, playlist, playlist_items, p_keys, uri):
        log.debug('%s.on_removed(uri: %r)', self.media, uri)

        # Find matching items in watchlist
        for p_item in self.match(playlist_items, p_keys):
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
