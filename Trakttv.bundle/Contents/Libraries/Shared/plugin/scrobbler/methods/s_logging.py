from plugin.core.helpers.variable import to_integer
from plugin.core.message import InterfaceMessages
from plugin.managers.action import ActionManager
from plugin.managers.session.s_logging import LSessionManager
from plugin.scrobbler.core import SessionEngine
from plugin.scrobbler.core.constants import IGNORED_EVENTS
from plugin.scrobbler.methods.core.base import Base

from datetime import datetime, timedelta
from plex_activity import Activity
import logging


log = logging.getLogger(__name__)


class Logging(Base):
    name = 'logging'

    def __init__(self):
        Activity.on('logging.playing', self.on_playing)

        self.engine = SessionEngine()

    def on_playing(self, info):
        if InterfaceMessages.critical:
            return

        # Create or retrieve existing session
        session = LSessionManager.get.or_create(info, fetch=True)

        if not session:
            return

        # Validate session
        if session.updated_at is None or (datetime.utcnow() - session.updated_at) > timedelta(minutes=5):
            log.info('Updating session, last update was over 5 minutes ago')
            LSessionManager.update(session, info, fetch=True)
            return

        if session.duration is None or session.view_offset is None:
            # Update session
            LSessionManager.update(session, info, fetch=lambda s, i: (
                s.rating_key != to_integer(i.get('ratingKey')) or
                s.duration is None
            ))
            return

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

        if state in IGNORED_EVENTS:
            log.debug('Ignored "%s" event: %r', state, info)
            return []

        # Validate `view_offset`
        view_offset = to_integer(info.get('viewOffset'))

        if view_offset is None:
            log.info('Event has an invalid view offset %r', view_offset)
            return []

        # Check for session `view_offset` jump
        if cls.session_jumped(session, info.get('viewOffset')):
            return []

        # Build event
        return [
            (state, {
                'rating_key': to_integer(info.get('ratingKey')),
                'view_offset': view_offset
            })
        ]

    @classmethod
    def test(cls):
        return True
