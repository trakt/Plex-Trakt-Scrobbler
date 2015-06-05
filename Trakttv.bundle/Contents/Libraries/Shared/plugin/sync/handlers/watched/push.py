from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, MediaHandler, bind

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    def push(self, rating_key, p_item, t_item):
        log.debug('push(%r, %r, %r)', rating_key, p_item, t_item)


class Movies(Base):
    media = SyncMedia.Movies


class Episodes(Base):
    media = SyncMedia.Episodes


class Push(DataHandler):
    data = SyncData.Watched
    mode = SyncMode.Push

    children = [
        Movies,
        Episodes
    ]
