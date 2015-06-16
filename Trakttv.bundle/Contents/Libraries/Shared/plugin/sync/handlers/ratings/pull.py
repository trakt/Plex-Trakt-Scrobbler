from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, PullHandler, bind
from plugin.sync.handlers.ratings.base import RatingsHandler

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(PullHandler, RatingsHandler):
    @staticmethod
    def build_action(action, p_item, p_value, t_value, **kwargs):
        data = {}

        if action in ['added', 'changed']:
            if type(t_value) is tuple:
                data['t_previous'], data['t_value'] = t_value
            else:
                data['t_value'] = t_value

        if action == 'changed':
            data['p_value'] = p_value

        data.update(kwargs)
        return data

    @staticmethod
    def rate(key, value):
        return Plex['library'].rate(key, value)


class Movies(Base):
    media = SyncMedia.Movies

    @bind('added')
    def on_added(self, key, t_value):
        log.debug('Movies.on_added(%r, %r)', key, t_value)

        return self.rate(key, t_value)

    @bind('changed', [SyncMode.FastPull])
    def on_changed(self, key, p_value, t_previous, t_value):
        log.debug('Movies.on_changed(%r, %r, %r, %r)', key, p_value, t_previous, t_value)

        return self.rate(key, t_value)

    @bind('removed', [SyncMode.FastPull])
    def on_removed(self, key):
        log.debug('Movies.on_removed(%r)', key)

        return self.rate(key, 0)


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added')
    def on_added(self, key, t_value):
        log.debug('Episodes.on_added(%r, %r)', key, t_value)

        return self.rate(key, t_value)

    @bind('changed', [SyncMode.FastPull])
    def on_changed(self, key, p_value, t_previous, t_value):
        log.debug('Episodes.on_changed(%r, %r, %r, %r)', key, p_value, t_previous, t_value)

        return self.rate(key, t_value)

    @bind('removed', [SyncMode.FastPull])
    def on_removed(self, key):
        log.debug('Episodes.on_removed(%r)', key)

        return self.rate(key, 0)


class Pull(DataHandler):
    data = SyncData.Ratings
    mode = [SyncMode.FastPull, SyncMode.Pull]

    children = [
        Movies,
        Episodes
    ]
