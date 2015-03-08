from plugin.core.helpers.variable import to_integer
from plugin.managers import ActionManager, WSessionManager
from plugin.scrobbler.core.engine import SessionEngine
from plugin.scrobbler.methods.core.base import Base

from plex import Plex
from plex_activity import Activity
import logging

log = logging.getLogger(__name__)


class WebSocket(Base):
    def __init__(self):
        Activity.on('websocket.playing', self.on_playing)

        self.engine = SessionEngine()

    def on_playing(self, info):
        # Create or retrieve existing session
        session = WSessionManager.get.or_create(info, fetch=True)

        actions = self.engine.process(session, self.to_events(info))

        for action, payload in actions:
            # Build request for the event
            request = self.build_request(session, rating_key=payload.get('rating_key'))

            # Queue request to be sent
            ActionManager.queue('/'.join(['scrobble', action]), request, session)

        # Update session
        WSessionManager.update(session, info)

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
