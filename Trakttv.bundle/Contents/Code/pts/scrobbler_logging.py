from core.helpers import get_pref
from core.logger import Logger
from data.watch_session import WatchSession
from plex.objects.client import Client
from plex.objects.user import User
from pts.scrobbler import Scrobbler, ScrobblerMethod

from plex import Plex
from plex_activity import Activity
from plex_metadata import Guid, Metadata


log = Logger('pts.scrobbler_logging')


class LoggingScrobbler(ScrobblerMethod):
    name = 'logging'

    def __init__(self):
        super(LoggingScrobbler, self).__init__()

        Activity.on('logging.playing', self.update)

    @classmethod
    def test(cls):
        # Try enable logging
        if not Plex[':/prefs'].set('logDebug', True):
            log.warn('Unable to enable logging')

        # Test if logging is enabled
        log_debug = Plex[':/prefs'].get('logDebug')

        if log_debug and not log_debug.value:
            log.warn('Debug logging not enabled, unable to use logging activity method.')
            return False

        return True

    def create_session(self, info):
        if not info.get('ratingKey'):
            log.warn('Invalid ratingKey provided from activity info')
            return None

        # Metadata
        metadata = Metadata.get(info['ratingKey'])

        # Guid
        guid = Guid.parse(metadata.guid) if metadata else None

        ws = WatchSession.from_info(info, metadata, guid, info['ratingKey'])
        ws.skip = not metadata

        # Fetch client by `machineIdentifier`
        ws.client = Plex.clients().get(info['machineIdentifier'])

        if not ws.client:
            # Create dummy client from `info`
            ws.client = Client(Plex.client, 'clients')
            ws.client.name = info.get('client', None)
            ws.client.machine_identifier = info.get('machineIdentifier', None)

            ws.client.address = info.get('address', None)
            ws.client.port = info.get('port', None)

        # Create dummy user from `info`
        ws.user = User(Plex.client, 'accounts')
        ws.user.id = info['user_id']
        ws.user.title = info['user_name']

        ws.save()

        log.debug('created session: %s', ws)
        return ws

    def session_valid(self, ws, info):
        if ws.rating_key != info['ratingKey']:
            log.debug('Invalid Session: Media changed')
            self.finish(ws)
            return False

        if ws.skip and info.get('state') == 'stopped':
            log.debug('Invalid Session: Media stopped')
            return False

        if not ws.metadata:
            if ws.skip:
                return True

            log.debug('Invalid Session: Missing metadata')
            return False

        if not ws.metadata.duration or ws.metadata.duration <= 0:
            log.debug('Invalid Session: Invalid duration')
            return False

        return True

    def get_session(self, info):
        session = WatchSession.load('logging-%s' % info.get('machineIdentifier'))

        if session and not self.session_valid(session, info):
            session.delete_instance()
            session = None
            log.debug('Session deleted')

        if not session:
            session = self.create_session(info)

            if not session:
                return None

        if not session or session.skip:
            return None

        return session

    def update(self, info):
        # Ignore if scrobbling is disabled
        if not get_pref('scrobble'):
            return

        ws = self.get_session(info)
        if not ws:
            log.trace('Invalid or ignored session, nothing to do')
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
        if self.offset_jumped(ws, info['time']):
            log.info('View offset jump detected, ignoring the state update')
            ws.save()
            return

        ws.last_view_offset = info['time']

        # Calculate progress
        if not self.update_progress(ws, info['time']):
            log.warn('Error while updating session progress, queued session to be updated')
            ws.update_required = True
            ws.save()
            return

        action = self.get_action(ws, info['state'])

        if action:
            self.handle_action(ws, action)
        else:
            log.debug(self.status_message(ws, info.get('state'))('Nothing to do this time for %s'))
            ws.save()

        self.handle_state(ws, info['state'])

Scrobbler.register(LoggingScrobbler, weight=1)
