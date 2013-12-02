from data.client import Client
from data.watch_session import WatchSession
from plex.media_server import PMS
from pts.scrobbler import Scrobbler


class LoggingScrobbler(Scrobbler):
    def create_session(self, info):
        client = None
        if info.get('machineIdentifier'):
            client = PMS.client(info['machineIdentifier'])
        else:
            Log.Info('No machineIdentifier available, client filtering not available')

        return WatchSession.from_info(
            info,
            PMS.metadata(info['ratingKey']),
            client
        )

    def session_valid(self, session, info):
        if session.item_key != info['ratingKey']:
            Log.Debug('Invalid Session: Media changed')
            return False

        if session.skip and info.get('state') == 'stopped':
            Log.Debug('Invalid Session: Media stopped')
            return False

        if not session.metadata:
            Log.Debug('Invalid Session: Missing metadata')
            return False

        if session.metadata.get('duration', 0) <= 0:
            Log.Debug('Invalid Session: Invalid duration')
            return False

        return True

    def get_session(self, info):
        session = WatchSession.load('logging-%s' % info.get('machineIdentifier'))

        if session:
            if not self.session_valid(session, info):
                session.delete()
                session = None
                Log.Info('Session deleted')

            if not session or session.skip:
                return None

        else:
            session = self.create_session(info)

        return session

    def update(self, info):
        session = self.get_session(info)
        if not session:
            Log.Info('Invalid session, ignoring')
            return

        # Ensure we are only scrobbling for the client listed in preferences
        if not self.valid_client(session):
            Log.Info('Ignoring item (%s) played by other client: %s' % (
                session.get_title(),
                session.client.name if session.client else None
            ))
            session.skip = True
            session.save()
            return

        media_type = session.get_type()

        # Check if we are scrobbling a known media type
        if not media_type:
            Log.Info('Playing unknown item, will not be scrobbled: "%s"' % session.get_title())
            session.skip = True
            return

        # Calculate progress
        if not self.update_progress(session, info['time']):
            Log.Warn('Error while updating session progress, queued session to be updated')
            return

        action = self.get_action(session, info['state'])

        if action:
            self.handle_action(session, media_type, action, info['state'])
        else:
            Log.Debug('%s Nothing to do this time for %s' % (
                self.get_status_label(session, info.get('state')),
                session.get_title()
            ))
            session.save()

        if self.handle_state(session, info['state']) or action:
            session.save()
            Dict.Save()
