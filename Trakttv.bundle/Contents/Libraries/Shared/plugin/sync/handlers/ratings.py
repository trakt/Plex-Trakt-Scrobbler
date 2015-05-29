from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, MediaHandler, bind

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, key, p_value, t_value):
        kwargs = {
            'key': key
        }

        if action in ['added', 'changed']:
            if type(t_value) is tuple:
                kwargs['t_previous'], kwargs['t_value'] = t_value
            else:
                kwargs['t_value'] = t_value

        if action == 'changed':
            kwargs['p_value'] = p_value

        return kwargs

    @staticmethod
    def get_operands(p_item, t_item):
        p_rating = p_item.get('settings', {}).get('rating')

        # Retrieve trakt rating from item
        if type(t_item) is dict:
            t_rating = t_item.get('rating')
        else:
            t_rating = t_item.rating if t_item else None

        # Convert trakt `Rating` objects to plain rating values
        if type(t_rating) is tuple:
            t_rating = tuple([
                (r.value if r else None)
                for r in t_rating
            ])
        else:
            t_rating = t_rating.value if t_rating else None

        return p_rating, t_rating

    @staticmethod
    def rate(key, value):
        return Plex['library'].rate(key, value)

    #
    # Modes
    #

    def fast_pull(self, action, rating_key, p_item, t_item):
        log.debug('fast_pull(%r, %r, %r, %r)', action, rating_key, p_item, t_item)

        if not action:
            # No action provided
            return

        # Retrieve properties
        p_rating, t_rating = self.get_operands(p_item, t_item)

        # Execute action
        self.execute_action(action, (
            action,
            rating_key,
            p_rating,
            t_rating
        ))

    def pull(self, rating_key, p_item, t_item):
        # Retrieve properties
        p_rating, t_rating = self.get_operands(p_item, t_item)

        # Determine performed action
        action = self.get_action(p_rating, t_rating)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(action, (
            action,
            rating_key,
            p_rating,
            t_rating
        ))


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


class Ratings(DataHandler):
    data = SyncData.Ratings

    children = [
        Movies,
        Episodes
    ]
