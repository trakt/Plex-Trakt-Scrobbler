from data.watch_session import WatchSession
from plex.media_server import PlexMediaServer
from pts.scrobbler import Scrobbler


class LoggingScrobbler(Scrobbler):
    def create_session(self, info):
        return WatchSession(
            'logging',
            info['ratingKey'],
            PlexMediaServer.metadata(info['ratingKey']),
            info['state'],
            client_id=info.get('client_id')
        )

    def session_changed(self, session, info):
        if session.item_key != info['ratingKey']:
            return True

        return False

    def get_session(self, info):
        session = WatchSession.load('logging')

        if session:
            if self.session_changed(session, info):
                session.delete()
                session = None

            if not session or session.skip:
                return None

        else:
            session = self.create_session(info)

        return session

    def update(self, info):
        Log.Info('[LoggingScrobbler](update) info: %s' % info)

        session = self.get_session(info)
        if not session:
            Log.Info('Invalid session, unable to continue')
            return

        media_type = session.get_type()

        # Check if we are scrobbling a known media type
        if not media_type:
            Log.Info('Playing unknown item, will not be scrobbled: ' + session.get_title())
            session.skip = True
            return

        # Calculate progress
        session.progress = int(round((float(info['time']) / (session.metadata['duration'] * 60 * 1000)) * 100, 0))

        action = self.get_action(session, info['state'])

        if info['state'] == 'playing':
            session.paused_since = None

        # No action needed, exit
        if not action:
            Log.Debug('Nothing to do this time for ' + session.get_title())
            session.save()
            return

        if self.handle_action(session, media_type, action, info['state']):
            Dict.Save()
