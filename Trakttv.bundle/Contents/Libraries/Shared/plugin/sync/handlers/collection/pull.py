from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.collection.base import CollectionHandler
from plugin.sync.handlers.core.base import DataHandler, PullHandler

import logging

log = logging.getLogger(__name__)


class Base(PullHandler, CollectionHandler):
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


class Pull(DataHandler):
    data = SyncData.Collection
    mode = [SyncMode.FastPull, SyncMode.Pull]

    children = [
        Movies,
        Episodes
    ]
