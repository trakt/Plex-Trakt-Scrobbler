from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import bind
from plugin.sync.handlers.core.base import DataHandler, MediaHandler

import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, p_guid, p_item, p_value, **kwargs):
        data = {}

        if action in ['added', 'changed']:
            data['p_guid'] = p_guid
            data['p_item'] = p_item

            data['p_value'] = p_value

        data.update(kwargs)
        return data

    @staticmethod
    def get_operands(p_item, t_item):
        # Retrieve plex rating from item
        p_rating = p_item.get('settings', {}).get('rating')

        # Convert rating to integer
        if p_rating is not None:
            p_rating = int(p_rating)

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

    def get_action(self, p_value, t_value):
        if p_value is None and t_value is not None:
            return 'removed'

        if p_value is not None and t_value is None:
            return 'added'

        if p_value != t_value:
            return 'changed'

        return None

    def push(self, p_item, t_item, **kwargs):
        # Retrieve properties
        p_rating, t_rating = self.get_operands(p_item, t_item)

        # Determine performed action
        action = self.get_action(p_rating, t_rating)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(
            action,

            p_item=p_item,
            p_value=p_rating,
            t_value=t_rating,
            **kwargs
        )


class Movies(Base):
    media = SyncMedia.Movies

    @bind('added', [SyncMode.Push])
    def on_added(self, key, p_guid, p_item, p_value, t_value, **kwargs):
        log.debug('Movies.on_added(%r, ...)', key)

        if t_value:
            return

        self.store_movie('add', p_guid,
            p_item,
            rating=p_value
        )


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added', [SyncMode.Push])
    def on_added(self, key, p_guid, identifier, p_show, p_value, t_value, **kwargs):
        log.debug('Episodes.on_added(%r, ...)', key)

        if t_value:
            return

        self.store_episode('add', p_guid,
            identifier, p_show,
            rating=p_value
        )


class Push(DataHandler):
    data = SyncData.Ratings
    mode = SyncMode.Push

    children = [
        Movies,
        Episodes
    ]
