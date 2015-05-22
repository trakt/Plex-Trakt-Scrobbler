from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.handlers.core.base import DataHandler, MediaHandler

import logging

log = logging.getLogger(__name__)


class Movies(MediaHandler):
    media = SyncMedia.Movies

    def pull(self, rating_key, p_settings, t_item):
        log.debug('pull(%s, %r, %r)', rating_key, p_settings, t_item)

        # Nothing to do
        return True


class Collection(DataHandler):
    data = SyncData.Collection

    children = [
        Movies
    ]
