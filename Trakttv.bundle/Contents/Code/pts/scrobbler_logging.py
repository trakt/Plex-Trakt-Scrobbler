from core.eventing import EventManager
from core.helpers import get_pref
from core.logger import Logger
from data.watch_session import WatchSession
from plex.plex_media_server import PlexMediaServer
from plex.plex_metadata import PlexMetadata
from plex.plex_preferences import PlexPreferences
from pts.scrobbler import Scrobbler, ScrobblerMethod


log = Logger('pts.scrobbler_logging')


class LoggingScrobbler(ScrobblerMethod):
    name = 'LoggingScrobbler'

    def __init__(self):
        super(LoggingScrobbler, self).__init__()

        EventManager.subscribe('scrobbler.logging.update', self.update)

    @classmethod
    def test(cls):
        # Try enable logging
        if not PlexPreferences.log_debug(True):
            log.warn('Unable to enable logging')

        # Test if logging is enabled
        if not PlexPreferences.log_debug():
            log.warn('Debug logging not enabled, unable to use logging activity method.')
            return False

        return True

    def create_session(self, info):
        if not info.get('ratingKey'):
            log.warn('Invalid ratingKey provided from activity info')
            return None

        skip = False

        # Client
        client = None
        if info.get('machineIdentifier'):
            client = PlexMediaServer.get_client(info['machineIdentifier'])
        else:
            log.info('No machineIdentifier available, client filtering not available')

        # Metadata
        metadata = None

        try:
            metadata = PlexMetadata.get(info['ratingKey'])

            if metadata:
                metadata = metadata.to_dict()
        except NotImplementedError, e:
            # metadata not supported (music, etc..)
            log.debug('%s, ignoring session' % e.message)
            skip = True

        session = WatchSession.from_info(info, metadata, client)
        session.skip = skip
        session.save()

        return session

    def session_valid(self, session, info):
        if session.item_key != info['ratingKey']:
            log.debug('Invalid Session: Media changed')
            return False

        if session.skip and info.get('state') == 'stopped':
            log.debug('Invalid Session: Media stopped')
            return False

        if not session.metadata:
            if session.skip:
                return True

            log.debug('Invalid Session: Missing metadata')
            return False

        if session.metadata.get('duration', 0) <= 0:
            log.debug('Invalid Session: Invalid duration')
            return False

        return True

    def get_session(self, info):
        session = WatchSession.load('logging-%s' % info.get('machineIdentifier'))

        if session and not self.session_valid(session, info):
            session.delete()
            session = None
            log.debug('Session deleted')

        if not session:
            session = self.create_session(info)

            if not session:
                return None

        if not session or session.skip:
            return None

        return session

    def valid(self, session):
        # Check filters
        if not self.valid_client(session) or\
           not self.valid_section(session):
            session.skip = True
            session.save()
            return False

        return True

    def update(self, info):
        # Ignore if scrobbling is disabled
        if not get_pref('scrobble'):
            return

        session = self.get_session(info)
        if not session:
            log.trace('Invalid or ignored session, nothing to do')
            return

        # Validate session (check filters)
        if not self.valid(session):
            return

        media_type = session.get_type()

        # Check if we are scrobbling a known media type
        if not media_type:
            log.info('Playing unknown item, will not be scrobbled: "%s"' % session.get_title())
            session.skip = True
            return

        # Check if the view_offset has jumped (#131)
        if self.offset_jumped(session, info['time']):
            log.info('View offset jump detected, ignoring the state update')
            session.save()
            return

        session.last_view_offset = info['time']

        # Calculate progress
        if not self.update_progress(session, info['time']):
            log.warn('Error while updating session progress, queued session to be updated')
            session.update_required = True
            session.save()
            return

        action = self.get_action(session, info['state'])

        if action:
            self.handle_action(session, media_type, action, info['state'])
        else:
            log.debug(self.status_message(session, info.get('state'))('Nothing to do this time for %s'))
            session.save()

        if self.handle_state(session, info['state']) or action:
            Dict.Save()

Scrobbler.register(LoggingScrobbler, weight=1)
