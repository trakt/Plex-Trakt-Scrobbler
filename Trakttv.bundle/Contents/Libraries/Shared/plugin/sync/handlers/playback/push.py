from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, PushHandler, bind
from plugin.sync.handlers.playback.base import PlaybackHandler

import logging

log = logging.getLogger(__name__)


class Base(PushHandler, PlaybackHandler):
    def push(self, p_item, t_item, **kwargs):
        # TODO Currently disabled, batch pushing of progress changes isn't supported on trakt
        return True


class Movies(Base):
    media = SyncMedia.Movies

    @bind('added', [SyncMode.Full, SyncMode.Push])
    def on_added(self, key, guid, p_item, p_value, t_value, **kwargs):
        log.debug('Movies.on_added(%r, ...)', key)

        if t_value:
            return

        log.debug(' - p_value: %r, t_value: %r', p_value, t_value)


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added', [SyncMode.Full, SyncMode.Push])
    def on_added(self, key, guid, identifier, p_show, p_value, t_value, **kwargs):
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
