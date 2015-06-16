from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, PushHandler, bind
from plugin.sync.handlers.watched.base import WatchedHandler

import logging

log = logging.getLogger(__name__)


class Base(PushHandler, WatchedHandler):
    @staticmethod
    def build_action(action, p_guid, p_item, p_value, **kwargs):
        data = {}

        if action in ['added', 'changed']:
            data['p_guid'] = p_guid
            data['p_item'] = p_item

            data['p_value'] = p_value

        data.update(kwargs)
        return data

    def push(self, p_item, t_item, **kwargs):
        # Retrieve properties
        p_viewed_at, t_viewed_at = self.get_operands(p_item, t_item)

        # Determine performed action
        action = self.get_action(p_viewed_at, t_viewed_at)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(
            action,

            p_item=p_item,
            p_value=p_viewed_at,
            t_value=t_viewed_at,
            **kwargs
        )


class Movies(Base):
    media = SyncMedia.Movies

    @bind('added', [SyncMode.Push])
    def on_added(self, key, p_guid, p_item, p_value, t_value, **kwargs):
        log.debug('Movies.on_added(%r, ...)', key)

        if t_value:
            return

        self.store_movie('add', p_guid,
            p_item,
            watched_at=p_value
        )

    @bind('removed', [SyncMode.Push])
    def on_removed(self, key, t_value, **kwargs):
        log.debug('Movies.on_removed(%r, ...)', key)


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added', [SyncMode.Push])
    def on_added(self, key, p_guid, identifier, p_show, p_value, t_value, **kwargs):
        log.debug('Episodes.on_added(%r, ...)', key)

        if t_value:
            return

        self.store_episode('add', p_guid,
            identifier, p_show,
            watched_at=p_value
        )

    @bind('removed', [SyncMode.Push])
    def on_removed(self, key, t_value, **kwargs):
        log.debug('Episodes.on_removed(%r, ...)', key)


class Push(DataHandler):
    data = SyncData.Watched
    mode = SyncMode.Push

    children = [
        Movies,
        Episodes
    ]
