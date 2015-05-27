from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.handlers.core.base import DataHandler, MediaHandler

import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    def pull(self, rating_key, p_item, t_item):
        # Nothing to do
        return True


class Movies(Base):
    media = SyncMedia.Movies


class Episodes(Base):
    media = SyncMedia.Episodes


class Collection(DataHandler):
    data = SyncData.Collection

    children = [
        Movies,
        Episodes
    ]
