from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.handlers.core.base import DataHandler, MediaHandler


class Movies(MediaHandler):
    media = SyncMedia.Movies


class Collection(DataHandler):
    data = SyncData.Collection

    children = [
        Movies
    ]
