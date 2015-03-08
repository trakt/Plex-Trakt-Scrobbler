from plugin.core.helpers.variable import to_integer
from plugin.scrobbler.core import SessionEngine
from plugin.scrobbler.methods.core.base import Base
from plugin.managers.session import LSessionManager

from plex_activity import Activity
import logging


log = logging.getLogger(__name__)


class Logging(Base):
    def __init__(self):
        Activity.on('logging.playing', self.on_playing)

        self.engine = SessionEngine()

    def on_playing(self, info):
        # Create or retrieve existing session
        session = LSessionManager.get.or_create(info, fetch=True)
        log.debug('session: %r', session)

        events = self.to_events(info)
        log.debug('events: %r', events)

        actions = self.engine.process(session, events)
        log.debug('actions: %r', actions)

    @staticmethod
    def to_events(info):
        state = info.get('state')

        if not state:
            log.warn('Event has an invalid state %r', state)
            return []

        return [
            (state, {
                'rating_key': to_integer(info.get('ratingKey'))
            })
        ]

    @classmethod
    def test(cls):
        return True
