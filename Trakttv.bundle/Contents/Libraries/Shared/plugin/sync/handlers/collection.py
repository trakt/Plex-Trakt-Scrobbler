from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.handlers.core.base import DataHandler, MediaHandler

import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    pass


class Movies(Base):
    media = SyncMedia.Movies

    def pull(self, rating_key, p_settings, t_item):
        log.debug('Movies.pull(%s, %r, %r)', rating_key, p_settings, t_item)

        # Nothing to do
        return True


class Episodes(Base):
    media = SyncMedia.Episodes

    def pull(self, rating_key, p_settings, t_item):
        log.debug('Episodes.pull(%s, %r, %r)', rating_key, p_settings, t_item)


class Collection(DataHandler):
    data = SyncData.Collection

    children = [
        Movies,
        Episodes
    ]
