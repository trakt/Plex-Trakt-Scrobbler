from plugin.core.helpers.variable import to_integer
from plugin.core.message import InterfaceMessages
from plugin.managers.action import ActionManager
from plugin.managers.session.base import UpdateSession
from plugin.managers.session.s_websocket import WSessionManager
from plugin.scrobbler.core.constants import IGNORED_EVENTS
from plugin.scrobbler.core.engine import SessionEngine
from plugin.scrobbler.methods.core.base import Base

from datetime import datetime, timedelta
from plex import Plex
from plex_activity import Activity
import logging

log = logging.getLogger(__name__)


class WebSocket(Base):
    name = 'websocket'

    def __init__(self):
        Activity.on('websocket.playing', self.on_playing)

        self.engine = SessionEngine()

    def on_playing(self, info):
        if InterfaceMessages.critical:
            return

        # Create or retrieve existing session
        session = WSessionManager.get.or_create(info, fetch=True)

        # Validate session
        if session.updated_at is None or (datetime.utcnow() - session.updated_at) > timedelta(minutes=5):
            log.info('Updating session, last update was over 5 minutes ago')
            WSessionManager.update(session, info, fetch=True)
            return

        if session.duration is None or session.view_offset is None:
            # Update session
            WSessionManager.update(session, info, fetch=lambda s, i: (
                s.rating_key != to_integer(i.get('ratingKey')) or
                s.duration is None
            ))
            return

        # Parse `info` to events
        events = self.to_events(session, info)

        if not events:
            return

        # Check for changed media
        media_changed = session.rating_key != to_integer(info.get('ratingKey'))

        # Parse `events`
        actions = self.engine.process(session, events)

        for action, payload in actions:
            # Build request for the event
            request = self.build_request(
                session,
                part=payload.get('part', 1),
                rating_key=payload.get('rating_key'),
                view_offset=payload.get('view_offset')
            )

            if not request:
                log.info('No request returned for action %r (payload: %r)', action, payload)
                continue

            # Queue request to be sent
            ActionManager.queue('/'.join(['scrobble', action]), request, session)

        # Update session
        WSessionManager.update(session, info, fetch=media_changed)

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

        # Check for session `view_offset` jump
        if cls.session_jumped(session, info.get('viewOffset')):
            return []

        # Retrieve event parameters
        view_offset = to_integer(info.get('viewOffset'))

        # Calculate current part number
        # TODO handle null values from session?
        part, _ = UpdateSession.get_part(session.duration, view_offset, session.part_count)

        # Build event
        return [
            (state, {
                'part': part,
                'rating_key': to_integer(info.get('ratingKey')),
                'view_offset': view_offset
            })
        ]

    @classmethod
    def test(cls):
        if Plex['status'].sessions() is None:
            log.info("Error while retrieving sessions, assuming WebSocket method isn't available")
            return False

        detail = Plex.detail()
        if detail is None:
            log.info('Error while retrieving server info for testing')
            return False

        if not detail.multiuser:
            log.info("Server info indicates multi-user support isn't available, WebSocket method not available")
            return False

        return True
