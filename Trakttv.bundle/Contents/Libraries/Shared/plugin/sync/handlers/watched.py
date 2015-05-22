from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.handlers.core.base import DataHandler, MediaHandler

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, rating_key, p_viewed_at, t_viewed_at):
        kwargs = {
            'rating_key': rating_key
        }

        if action in ['added', 'changed']:
            kwargs['t_viewed_at'] = t_viewed_at

        if action == 'changed':
            kwargs['p_viewed_at'] = p_viewed_at

        return kwargs

    @staticmethod
    def get_operands(p_settings, t_item):
        return (
            p_settings.get('last_viewed_at'),
            t_item.last_watched_at if t_item else None
        )


class Movies(Base):
    media = SyncMedia.Movies

    def pull(self, rating_key, p_settings, t_item):
        log.debug('pull(%s, %r, %r)', rating_key, p_settings, t_item)

        # Retrieve properties
        p_viewed_at, t_viewed_at = self.get_operands(p_settings, t_item)

        # Determine performed action
        action = self.get_action(p_viewed_at, t_viewed_at)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(action, **self.build_action(
            action,
            rating_key,
            p_viewed_at,
            t_viewed_at
        ))

    def on_added(self, rating_key, t_viewed_at):
        log.debug('on_added(%r, %r)', rating_key, t_viewed_at)

        return Plex['library'].scrobble(rating_key)

    def on_removed(self, rating_key):
        log.debug('on_removed(%r)', rating_key)

        raise NotImplementedError

    def on_changed(self, rating_key, p_viewed_at, t_viewed_at):
        log.debug('on_changed(%r, %r, %r)', rating_key, p_viewed_at, t_viewed_at)

        raise NotImplementedError


class Watched(DataHandler):
    data = SyncData.Watched

    children = [
        Movies
    ]
