from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.handlers.core.base import DataHandler, MediaHandler

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, rating_key, p_rating, t_rating):
        kwargs = {
            'rating_key': rating_key
        }

        if action in ['added', 'changed']:
            kwargs['t_rating'] = t_rating

        if action == 'changed':
            kwargs['p_rating'] = p_rating

        return kwargs

    @staticmethod
    def get_operands(p_settings, t_item):
        return (
            p_settings.get('rating'),
            t_item.rating.value if t_item and t_item.rating else None
        )

    @staticmethod
    def rate(rating_key, value):
        return Plex['library'].rate(rating_key, value)

    def pull(self, rating_key, p_settings, t_item):
        # Retrieve properties
        p_rating, t_rating = self.get_operands(p_settings, t_item)

        # Determine performed action
        action = self.get_action(p_rating, t_rating)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(action, **self.build_action(
            action,
            rating_key,
            p_rating,
            t_rating
        ))


class Movies(Base):
    media = SyncMedia.Movies

    def on_added(self, rating_key, t_rating):
        log.debug('Movies.on_added(%r, %r)', rating_key, t_rating)

        return self.rate(rating_key, t_rating)


class Episodes(Base):
    media = SyncMedia.Episodes

    def on_added(self, rating_key, t_rating):
        log.debug('Episodes.on_added(%r, %r)', rating_key, t_rating)

        return self.rate(rating_key, t_rating)


class Ratings(DataHandler):
    data = SyncData.Ratings

    children = [
        Movies,
        Episodes
    ]
