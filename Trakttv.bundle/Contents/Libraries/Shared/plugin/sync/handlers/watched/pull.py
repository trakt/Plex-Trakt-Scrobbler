from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode, SyncActionMode
from plugin.sync.handlers.core import DataHandler, PullHandler, bind
from plugin.sync.handlers.watched.base import WatchedHandler

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(PullHandler, WatchedHandler):
    @staticmethod
    def build_action(action, p_item, t_value, **kwargs):
        data = {}

        if action in ['added', 'changed']:
            if type(t_value) is tuple:
                data['t_previous'], data['t_value'] = t_value
            else:
                data['t_value'] = t_value

        data.update(kwargs)
        return data

    def scrobble(self, key):
        action_mode = self.configuration['sync.action.mode']

        if action_mode == SyncActionMode.Update:
            return Plex['library'].scrobble(key)

        if action_mode == SyncActionMode.Log:
            log.info('[%s] scrobble()', key)
            return True

        raise NotImplementedError('Unable to update plex, action mode %r not supported', action_mode)

    def unscrobble(self, key):
        action_mode = self.configuration['sync.action.mode']

        if action_mode == SyncActionMode.Update:
            return Plex['library'].unscrobble(key)

        if action_mode == SyncActionMode.Log:
            log.info('[%s] unscrobble()', key)
            return True

        raise NotImplementedError('Unable to update plex, action mode %r not supported', action_mode)

    #
    # Handlers
    #

    @bind('added')
    def on_added(self, key, p_value, t_value, **kwargs):
        log.debug('%s.on_added(%r, %r, %r)', self.media, key, p_value, t_value)

        if p_value is not None:
            # Already scrobbled
            return

        return self.scrobble(key)

    @bind('removed', [SyncMode.Full, SyncMode.FastPull])
    def on_removed(self, key, p_value, **kwargs):
        log.debug('%s.on_removed(%r, %r)', self.media, key, p_value)

        if p_value is None:
            # Already un-scrobbled
            return

        return self.unscrobble(key)


class Movies(Base):
    media = SyncMedia.Movies


class Episodes(Base):
    media = SyncMedia.Episodes


class Pull(DataHandler):
    data = SyncData.Watched
    mode = [SyncMode.FastPull, SyncMode.Pull]

    children = [
        Movies,
        Episodes
    ]
