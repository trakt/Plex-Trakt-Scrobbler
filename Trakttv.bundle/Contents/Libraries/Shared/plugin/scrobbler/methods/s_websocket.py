from plugin.managers import ActionManager
from plugin.scrobbler.methods.core.base import Base
from plugin.managers.session import SessionManager

from plex import Plex
from plex_activity import Activity
import logging

log = logging.getLogger(__name__)


class WebSocket(Base):
    def __init__(self):
        Activity.on('websocket.playing', self.on_playing)

    def on_playing(self, info):
        session = SessionManager.from_websocket(info)
        log.debug('session: %r', session)

        event = ActionManager.decide(session)
        log.debug('event: %r', event)

        ActionManager.queue(session, event)

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
