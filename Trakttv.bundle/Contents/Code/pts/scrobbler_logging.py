from data.client import Client
from data.watch_session import WatchSession
from plex.media_server import PlexMediaServer
from pts.scrobbler import Scrobbler


class LoggingScrobbler(Scrobbler):
    def create_session(self, info):
        client = None
        if info.get('machineIdentifier'):
            PlexMediaServer.client(info['machineIdentifier'])
        else:
            Log.Info('No machineIdentifier available, client filtering not available')

        return WatchSession.from_info(
            info,
            PlexMediaServer.metadata(info['ratingKey']),
            client
        )

    def session_valid(self, session, info):
        if session.item_key != info['ratingKey']:
            Log.Debug('Invalid Session: Media changed')
            return False

        if session.skip and info.get('state') == 'stopped':
            Log.Debug('Invalid Session: Media stopped')
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
            Log.Info('Invalid session, unable to continue')
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
        session.progress = int(round((float(info['time']) / (session.metadata['duration'] * 60 * 1000)) * 100, 0))

        action = self.get_action(session, info['state'])

        if info['state'] == 'playing':
            session.paused_since = None

        # No action needed, exit
        if not action:
            Log.Debug('%s Nothing to do this time for %s' % (
                self.get_status_label(session, info.get('state')),
                session.get_title()
            ))
            session.save()
            return

        if self.handle_action(session, media_type, action, info['state']):
            Dict.Save()
