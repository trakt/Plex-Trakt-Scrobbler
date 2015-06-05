from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, MediaHandler, bind

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, key, p_value, t_value):
        kwargs = {
            'key': key,

            'p_value': p_value
        }

        if action in ['added', 'changed']:
            kwargs['t_value'] = t_value

        return kwargs

    @staticmethod
    def get_operands(p_item, t_item):
        p_viewed_at = p_item.get('settings', {}).get('last_viewed_at')

        # Retrieve trakt `viewed_at` from item
        if type(t_item) is dict:
            t_viewed_at = t_item.get('last_watched_at')
        else:
            t_viewed_at = t_item.last_watched_at if t_item else None

        return p_viewed_at, t_viewed_at

    @staticmethod
    def scrobble(key):
        return Plex['library'].scrobble(key)

    @staticmethod
    def unscrobble(key):
        return Plex['library'].unscrobble(key)

    #
    # Modes
    #

    def fast_pull(self, action, rating_key, p_item, t_item):
        if not action:
            # No action provided
            return

        # Retrieve properties
        p_viewed_at, t_viewed_at = self.get_operands(p_item, t_item)

        # Execute action
        self.execute_action(action, (
            action,
            rating_key,
            p_viewed_at,
            t_viewed_at
        ))

    def pull(self, rating_key, p_item, t_item):
        # Retrieve properties
        p_viewed_at, t_viewed_at = self.get_operands(p_item, t_item)

        # Determine performed action
        action = self.get_action(p_viewed_at, t_viewed_at)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(action, (
            action,
            rating_key,
            p_viewed_at,
            t_viewed_at
        ))


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
