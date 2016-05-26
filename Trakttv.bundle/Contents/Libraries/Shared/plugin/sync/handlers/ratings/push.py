from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, PushHandler, bind
from plugin.sync.handlers.ratings.base import RatingsHandler

import logging

log = logging.getLogger(__name__)


class Base(PushHandler, RatingsHandler):
    pass


class Movies(Base):
    media = SyncMedia.Movies

    @bind('added', [SyncMode.Full, SyncMode.Push])
    def on_added(self, key, guid, p_item, p_value, t_value, **kwargs):
        log.debug('Movies.on_added(%r, ...)', key)

        if t_value:
            return

        self.store_movie('add', guid,
             key, p_item,
             rating=p_value
         )

    @bind('changed', [SyncMode.Full, SyncMode.Push])
    def on_changed(self, key, guid, p_item, p_value, **kwargs):
        log.debug('Movies.on_changed(%r, ...)', key)

        self.store_movie('add', guid,
             key, p_item,
             rating=p_value
         )


class Shows(Base):
    media = SyncMedia.Shows

    @bind('added', [SyncMode.Full, SyncMode.Push])
    def on_added(self, key, guid, p_item, p_value, t_value, **kwargs):
        log.debug('Shows.on_added(%r, ...)', key)

        if t_value:
            return

        self.store_show('add', guid,
            key, p_item,
            rating=p_value
        )

    @bind('changed', [SyncMode.Full, SyncMode.Push])
    def on_changed(self, key, guid, p_item, p_value, **kwargs):
        log.debug('Shows.on_changed(%r, ...)', key)

        self.store_show('add', guid,
            key, p_item,
            rating=p_value
        )


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added', [SyncMode.Full, SyncMode.Push])
    def on_added(self, key, guid, identifier, p_show, p_item, p_value, t_value, **kwargs):
        log.debug('Episodes.on_added(%r, ...)', key)

        if t_value:
            return

        self.store_episode('add', guid,
            identifier, key,
            p_show, p_item,
            rating=p_value
        )

    @bind('changed', [SyncMode.Full, SyncMode.Push])
    def on_changed(self, key, guid, identifier, p_show, p_item, p_value, **kwargs):
        log.debug('Episodes.on_changed(%r, ...)', key)

        self.store_episode('add', guid,
            identifier, key,
            p_show, p_item,
            rating=p_value
        )


class Push(DataHandler):
    data = SyncData.Ratings
    mode = SyncMode.Push

    children = [
        Movies,

        Shows,
        Episodes
    ]
