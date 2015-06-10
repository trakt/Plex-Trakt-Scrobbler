from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core.base import DataHandler, MediaHandler

import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    def push(self, p_item, t_item, **kwargs):
        log.debug('push(%r, %r, %r)', p_item, t_item, kwargs)


class Movies(Base):
    media = SyncMedia.Movies


class Episodes(Base):
    media = SyncMedia.Episodes


class Push(DataHandler):
    data = SyncData.Ratings
    mode = SyncMode.Push

    children = [
        Movies,
        Episodes
    ]
