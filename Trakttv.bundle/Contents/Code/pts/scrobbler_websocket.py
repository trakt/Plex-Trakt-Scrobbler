from core.helpers import get_pref, try_convert
from core.logger import Logger
from data.watch_session import WatchSession
from pts.scrobbler import Scrobbler, ScrobblerMethod

from plex import Plex
from plex_activity import Activity
from plex_metadata import Guid, Metadata


log = Logger('pts.scrobbler_websocket')


class WebSocketScrobbler(ScrobblerMethod):
    name = 'websocket'

    def __init__(self):
        super(WebSocketScrobbler, self).__init__()

        Activity.on('websocket.playing', self.update)

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

    def create_session(self, session_key, state):
        """
        :type session_key: str
        :type state: str

        :rtype: WatchSession or None
        """

        log.debug('Creating a WatchSession for the current media')

        item = Plex['status'].sessions().get(session_key)
        if not item:
            log.warn('Unable to find session with key "%s"', session_key)
            return None

        # Metadata
        metadata = Metadata.get(item.rating_key)

        # Guid
        guid = Guid.parse(metadata.guid) if metadata else None

        # Create WatchSession
        ws = WatchSession.from_session(item.session, metadata, guid, item.rating_key, state)
        ws.skip = not metadata

        # Fetch client by `machineIdentifier`
        ws.client = Plex.clients().get(item.session.player.machine_identifier)

        ws.save()

        log.debug('created session: %s', ws)
        return ws

    def update_session(self, ws, view_offset):
        log.debug('Trying to update the current WatchSession (session key: %s)' % ws.key)

        sessions = Plex['status'].sessions()

        if sessions is None:
            log.warn('Unable to retrieve sessions')
            return False

        session = sessions.get(ws.key)

        if not session:
            log.warn('Session was not found on media server')
            self.finish(ws)
            return False

        log.debug('last item key: %s, current item key: %s' % (ws.rating_key, session.rating_key))

        if ws.rating_key != session.rating_key:
            log.debug('Invalid Session: Media changed')
            self.finish(ws)
            return False

        ws.last_view_offset = view_offset
        ws.update_required = False

        return True

    def session_valid(self, session):
        if not session.metadata:
            if session.skip:
                return True

            log.debug('Invalid Session: Missing metadata')
            return False

        if not session.metadata.duration or session.metadata.duration <= 0:
            log.debug('Invalid Session: Invalid duration')
            return False

        return True

    def get_session(self, session_key, state, view_offset):
        session = WatchSession.load(session_key)

        if not session:
            session = self.create_session(session_key, state)

            if not session:
                return None

        update_session = False

        # Update session when view offset goes backwards
        if session.last_view_offset and session.last_view_offset > view_offset:
            log.debug('View offset has gone backwards (last: %s, cur: %s)' % (
                session.last_view_offset, view_offset
            ))

            update_session = True

        # Update session on missing metadata + session skip
        if not session.metadata and session.skip:
            update_session = True

        # First try update the session if the media hasn't changed
        # otherwise delete the session
        if update_session and not self.update_session(session, view_offset):
            log.debug('Media changed, deleting the session')
            session.delete_instance()
            return None

        # Delete session if invalid
        if not self.session_valid(session):
            session.delete_instance()
            return None

        if session.skip:
            return None

        if state == 'playing' and session.update_required:
            log.debug('Session update required, updating the session...')

            if not self.update_session(session, view_offset):
                log.debug('Media changed, deleting the session')
                session.delete_instance()
                return None

        return session

    def update(self, info):
        # Ignore if scrobbling is disabled
        if not get_pref('scrobble'):
            return

        session_key = try_convert(info.get('sessionKey'), int)
        state = info.get('state')
        view_offset = info.get('viewOffset')

        ws = self.get_session(session_key, state, view_offset)
        if not ws:
            log.trace('Invalid or ignored session, nothing to do')
            return

        # Ignore sessions flagged as 'skip'
        if ws.skip:
            return

        # Validate session (check filters)
        if not self.valid(ws):
            return

        # Check if we are scrobbling a known media type
        if not ws.type:
            log.info('Playing unknown item, will not be scrobbled: "%s"' % ws.title)
            ws.skip = True
            return

        # Check if the view_offset has jumped (#131)
        if self.offset_jumped(ws, view_offset):
            log.info('View offset jump detected, ignoring the state update')
            ws.save()
            return

        ws.last_view_offset = view_offset

        # Calculate progress
        if not self.update_progress(ws, view_offset):
            log.warn('Error while updating session progress, queued session to be updated')
            ws.update_required = True
            ws.save()
            return

        action = self.get_action(ws, state)

        if action:
            self.handle_action(ws, action)
        else:
            log.debug(self.status_message(ws, state)('Nothing to do this time for %s'))
            ws.save()

        self.handle_state(ws, state)

Scrobbler.register(WebSocketScrobbler, weight=10)
