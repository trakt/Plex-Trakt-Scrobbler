from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, MediaHandler, bind

import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, p_guid, p_item, p_value, **kwargs):
        data = {}

        if action in ['added', 'changed']:
            data['p_guid'] = p_guid
            data['p_item'] = p_item

            data['p_value'] = p_value

        data.update(kwargs)
        return data

    @staticmethod
    def get_operands(p_item, t_item):
        p_viewed_at = p_item.get('settings', {}).get('last_viewed_at')

        # Retrieve trakt `viewed_at` from item
        if type(t_item) is dict:
            t_viewed_at = t_item.get('last_watched_at')
        else:
            t_viewed_at = t_item.last_watched_at if t_item else None

        return p_viewed_at, t_viewed_at

    def get_action(self, p_value, t_value):
        if p_value is None and t_value is not None:
            return 'removed'

        if p_value is not None and t_value is None:
            return 'added'

        if p_value != t_value:
            return 'changed'

        return None

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
    def on_removed(self, key, p_value, t_value, **kwargs):
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
    def on_removed(self, key, p_value, t_value, **kwargs):
        log.debug('Episodes.on_removed(%r, ...)', key)


class Push(DataHandler):
    data = SyncData.Watched
    mode = SyncMode.Push

    children = [
        Movies,
        Episodes
    ]
