from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.handlers.core.base import DataHandler, MediaHandler

import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    #
    # Modes
    #

    def fast_pull(self, action, p_item, t_item, **kwargs):
        # Nothing to do
        return True

    def pull(self, p_item, t_item, **kwargs):
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
