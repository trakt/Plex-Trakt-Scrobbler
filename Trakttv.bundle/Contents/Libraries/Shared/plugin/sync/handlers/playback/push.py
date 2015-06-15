from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, bind
from plugin.sync.handlers.playback.base import PlaybackHandler

import logging

log = logging.getLogger(__name__)


class Base(PlaybackHandler):
    @staticmethod
    def build_action(action, p_guid, p_item, p_value, **kwargs):
        data = {}

        if action in ['added', 'changed']:
            data['p_guid'] = p_guid
            data['p_item'] = p_item

            data['p_value'] = p_value

        data.update(kwargs)
        return data

    def get_action(self, p_value, t_value):
        if p_value is None and t_value is not None:
            return 'removed'

        if p_value is not None and t_value is None:
            return 'added'

        if p_value != t_value:
            return 'changed'

        return None

    def push(self, p_item, t_item, **kwargs):
        # TODO Currently disabled, batch pushing of progress changes isn't supported on trakt
        return

        # Retrieve properties
        p_progress, t_progress = self.get_operands(p_item, t_item)

        # Determine performed action
        action = self.get_action(p_progress, t_progress)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(
            action,

            p_item=p_item,
            p_value=p_progress,
            t_value=t_progress,
            **kwargs
        )


class Movies(Base):
    media = SyncMedia.Movies

    @bind('added', [SyncMode.Push])
    def on_added(self, key, p_guid, p_item, p_value, t_value, **kwargs):
        log.debug('Movies.on_added(%r, ...)', key)

        if t_value:
            return

        log.debug(' - p_value: %r, t_value: %r', p_value, t_value)


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added', [SyncMode.Push])
    def on_added(self, key, p_guid, identifier, p_show, p_value, t_value, **kwargs):
        log.debug('Episodes.on_added(%r, ...)', key)

        if t_value:
            return

        log.debug(' - p_value: %r, t_value: %r', p_value, t_value)


class Push(DataHandler):
    data = SyncData.Playback
    mode = SyncMode.Push

    children = [
        Movies,
        Episodes
    ]
