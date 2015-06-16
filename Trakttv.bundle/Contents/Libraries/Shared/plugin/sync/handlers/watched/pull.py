from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, PullHandler, bind
from plugin.sync.handlers.watched.base import WatchedHandler

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(PullHandler, WatchedHandler):
    @staticmethod
    def build_action(action, t_value, **kwargs):
        data = {}

        if action in ['added', 'changed']:
            data['t_value'] = t_value

        data.update(kwargs)
        return data

    @staticmethod
    def scrobble(key):
        return Plex['library'].scrobble(key)

    @staticmethod
    def unscrobble(key):
        return Plex['library'].unscrobble(key)

    #
    # Modes
    #

    def fast_pull(self, action, p_item, t_item, **kwargs):
        if not action:
            # No action provided
            return

        # Retrieve properties
        p_viewed_at, t_viewed_at = self.get_operands(p_item, t_item)

        # Execute action
        self.execute_action(
            action,

            p_value=p_viewed_at,
            t_value=t_viewed_at,
            **kwargs
        )

    def pull(self, p_item, t_item, **kwargs):
        # Retrieve properties
        p_viewed_at, t_viewed_at = self.get_operands(p_item, t_item)

        # Determine performed action
        action = self.get_action(p_viewed_at, t_viewed_at)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(
            action,

            p_value=p_viewed_at,
            t_value=t_viewed_at,
            **kwargs
        )


class Movies(Base):
    media = SyncMedia.Movies

    @bind('added')
    def on_added(self, key, p_value, t_value):
        log.debug('Movies.on_added(%r, %r, %r)', key, p_value, t_value)

        if p_value is not None:
            # Already scrobbled
            return

        return self.scrobble(key)

    @bind('removed', [SyncMode.FastPull])
    def on_removed(self, key, p_value):
        log.debug('Movies.on_removed(%r, %r)', key, p_value)

        if p_value is None:
            # Already un-scrobbled
            return

        return self.unscrobble(key)


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added')
    def on_added(self, key, p_value, t_value):
        log.debug('Episodes.on_added(%r, %r, %r)', key, p_value, t_value)

        if p_value is not None:
            # Already scrobbled
            return

        return self.scrobble(key)

    @bind('removed', [SyncMode.FastPull])
    def on_removed(self, key, p_value):
        log.debug('Episodes.on_removed(%r, %r)', key, p_value)

        if p_value is None:
            # Already un-scrobbled
            return

        return self.unscrobble(key)


class Pull(DataHandler):
    data = SyncData.Watched
    mode = [SyncMode.FastPull, SyncMode.Pull]

    children = [
        Movies,
        Episodes
    ]
