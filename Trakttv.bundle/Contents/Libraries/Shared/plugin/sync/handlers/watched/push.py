from plugin.modules.core.manager import ModuleManager
from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, PushHandler, bind
from plugin.sync.handlers.watched.base import WatchedHandler

import logging

log = logging.getLogger(__name__)


class Base(PushHandler, WatchedHandler):
    def push(self, p_item, t_item, key, **kwargs):
        # Ensure item isn't currently being watched in plex
        if ModuleManager['sessions'].is_account_streaming(self.current.account.id, key):
            log.debug('Item %r is currently being watched, ignoring push watched handler', key)
            return

        super(Base, self).push(
            p_item, t_item,
            key=key,
            **kwargs
        )


class Movies(Base):
    media = SyncMedia.Movies

    @bind('added', [SyncMode.Full, SyncMode.Push])
    def on_added(self, key, guid, p_item, p_value, t_value, **kwargs):
        # Retrieve plex `view_count`
        p_settings = p_item.get('settings', {})
        p_view_count = p_settings.get('view_count', 0)

        log.debug('Movies.on_added(%r, ...) - p_view_count: %r, p_value: %r, t_value: %r', key, p_view_count, p_value, t_value)

        if t_value:
            return

        self.store_movie('add', guid,
            key, p_item,
            watched_at=p_value
        )

    @bind('removed', [SyncMode.Full, SyncMode.Push])
    def on_removed(self, key, t_value, **kwargs):
        log.debug('Movies.on_removed(%r, ...)', key)


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added', [SyncMode.Full, SyncMode.Push])
    def on_added(self, key, guid, identifier, p_show, p_item, p_value, t_value, **kwargs):
        # Retrieve plex `view_count`
        p_settings = p_item.get('settings', {})
        p_view_count = p_settings.get('view_count', 0)

        log.debug('Episodes.on_added(%r, ...) - p_view_count: %r, p_value: %r, t_value: %r', key, p_view_count, p_value, t_value)

        if t_value:
            return

        self.store_episode('add', guid,
            identifier, key,
            p_show, p_item,
            watched_at=p_value
        )

    @bind('removed', [SyncMode.Full, SyncMode.Push])
    def on_removed(self, key, t_value, **kwargs):
        log.debug('Episodes.on_removed(%r, ...)', key)


class Push(DataHandler):
    data = SyncData.Watched
    mode = SyncMode.Push

    children = [
        Movies,
        Episodes
    ]
