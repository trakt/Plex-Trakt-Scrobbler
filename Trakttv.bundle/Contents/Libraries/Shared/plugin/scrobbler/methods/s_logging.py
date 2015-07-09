from plugin.core.helpers.variable import to_integer
from plugin.managers import ActionManager
from plugin.scrobbler.core import SessionEngine
from plugin.scrobbler.methods.core.base import Base
from plugin.managers.session import LSessionManager

from plex_activity import Activity
import logging


log = logging.getLogger(__name__)


class Logging(Base):
    name = 'logging'

    def __init__(self):
        Activity.on('logging.playing', self.on_playing)

        self.engine = SessionEngine()

    def on_playing(self, info):
        # Create or retrieve existing session
        session = LSessionManager.get.or_create(info, fetch=True)

        # Parse `info` to events
        events = self.to_events(session, info)

        if not events:
            return

        # Parse `events`
        actions = self.engine.process(session, events)

        for action, payload in actions:
            # Build request for the event
            request = self.build_request(
                session,
                rating_key=payload.get('rating_key'),
                view_offset=payload.get('view_offset')
            )

            if not request:
                continue

            # Queue request to be sent
            ActionManager.queue('/'.join(['scrobble', action]), request, session)

        # Update session
        LSessionManager.update(session, info)

    @classmethod
    def to_events(cls, session, info):
        # Validate `state`
        state = info.get('state')

        if not state:
            log.warn('Event has an invalid state %r', state)
            return []

        # Check for session `view_offset` jump
        if cls.session_jumped(session, info.get('viewOffset')):
            return []

        # Build event
        return [
            (state, {
                'rating_key': to_integer(info.get('ratingKey')),
                'view_offset': to_integer(info.get('viewOffset'))
            })
        ]

    @classmethod
    def test(cls):
        return True
