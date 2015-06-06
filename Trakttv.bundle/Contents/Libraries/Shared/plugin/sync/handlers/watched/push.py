from plugin.core.helpers.variable import dict_path
from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, MediaHandler, bind

from datetime import datetime
import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, key, p_guid, p_item, p_value, t_value):
        kwargs = {
            'key': key,

            't_value': t_value
        }

        if action in ['added', 'changed']:
            kwargs['p_guid'] = p_guid
            kwargs['p_item'] = p_item

            kwargs['p_value'] = p_value

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

    def get_action(self, p_value, t_value):
        if p_value is None and t_value is not None:
            return 'removed'

        if p_value is not None and t_value is None:
            return 'added'

        if p_value != t_value:
            return 'changed'

        return None

    def push(self, rating_key, p_guid, p_item, t_item):
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

            p_guid,
            p_item,
            p_viewed_at,

            t_viewed_at
        ))


class Movies(Base):
    media = SyncMedia.Movies

    def store(self, action, p_guid, p_item, **kwargs):
        if 'title' not in p_item or 'year' not in p_item:
            log.warn('Missing "title" or "year" parameters on %r', p_item.rating_key)
            return False

        request = {
            'title': p_item['title'],
            'year': p_item['year'],

            'ids': {}
        }

        if not p_guid:
            log.warn('No GUID present on %r', p_item.rating_key)
            return False

        # Set identifier
        request['ids'][p_guid.agent] = p_guid.sid

        # Set extra attributes
        for key, value in kwargs.items():
            if type(value) is datetime:
                try:
                    # Convert `datetime` object to string
                    value = value.strftime('%Y-%m-%dT%H:%M:%S') + '.000-00:00'
                except Exception, ex:
                    log.warn('Unable to convert %r to string', value)
                    return False

            request[key] = value

        # Store artifact
        artifacts = dict_path(self.current.artifacts, [
            self.parent.data,
            action
        ])

        if 'movies' not in artifacts:
            artifacts['movies'] = []

        artifacts['movies'].append(request)
        return True

    @bind('added', [SyncMode.Push])
    def on_added(self, key, p_guid, p_item, p_value, t_value):
        log.debug('Movies.on_added(%r, %r, %r, %r, %r)', key, p_guid, p_item, p_value, t_value)

        if t_value:
            return

        self.store('add', p_guid, p_item, watched_at=p_value)

    @bind('removed', [SyncMode.Push])
    def on_removed(self, key, p_value, t_value):
        log.debug('Movies.on_removed(%r, %r, %r)', key, p_value, t_value)


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added', [SyncMode.Push])
    def on_added(self, key, p_value, t_value):
        log.debug('Episodes.on_added(%r, %r, %r)', key, p_value, t_value)

        if t_value:
            return

    @bind('removed', [SyncMode.Push])
    def on_removed(self, key, p_value, t_value):
        log.debug('Episodes.on_removed(%r, %r, %r)', key, p_value, t_value)


class Push(DataHandler):
    data = SyncData.Watched
    mode = SyncMode.Push

    children = [
        Movies,
        Episodes
    ]
