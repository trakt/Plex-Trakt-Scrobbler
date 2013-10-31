from core.pms import PMS
from plex.media_server import PlexMediaServer
from pts.scrobbler import Scrobbler
from data.watch_session import WatchSession


class WebSocketScrobbler(Scrobbler):
    def create_session(self, session_key, state):
        """
        :type session_key: str
        :type state: str

        :rtype: WatchSession or None
        """

        Log.Debug('Creating a WatchSession for the current media')

        video_section = PMS.get_video_session(session_key)
        if not video_section:
            return None

        player_section = video_section.findall('Player')
        if len(player_section):
            player_section = player_section[0]

        session = WatchSession.from_section(
            video_section, state,
            PlexMediaServer.metadata(video_section.get('ratingKey')),
            PlexMediaServer.client(player_section.get('machineIdentifier'))
        )
        session.save()

        return session

    def update_session(self, session, view_offset):
        Log.Debug('Trying to update the current WatchSession (session key: %s)' % session.key)

        video_section = PMS.get_video_session(session.key)

        Log.Debug('last item key: %s, current item key: %s' % (session.item_key, video_section.get('ratingKey')))

        if session.item_key != video_section.get('ratingKey'):
            return False

        session.last_view_offset = view_offset
        session.update_required = False

        return True

    def get_session(self, session_key, state, view_offset):
        session = WatchSession.load(session_key)

        if session:
            if session.last_view_offset and session.last_view_offset > view_offset:
                Log.Debug('View offset has gone backwards (last: %s, cur: %s)' % (
                    session.last_view_offset, view_offset
                ))

                # First try update the session if the media hasn't changed
                # otherwise delete the session
                if self.update_session(session, view_offset):
                    Log.Debug('Updated the current session')
                else:
                    Log.Debug('Deleted the current session')
                    session.delete()
                    session = None

            if not session or session.skip:
                return None

            if state == 'playing' and session.update_required:
                self.update_session(session, view_offset)
        else:
            session = self.create_session(session_key, state)

        return session

    def update(self, session_key, state, view_offset):
        session = self.get_session(session_key, state, view_offset)
        if not session:
            Log.Info('Invalid session, unable to continue')
            return

        # Ignore sessions flagged as 'skip'
        if session.skip:
            return

        # Ensure we are only scrobbling for the myPlex user listed in preferences
        if not self.valid_user(session):
            Log.Info('Ignoring item [%s](%s) played by other user: %s' % (
                session_key,
                session.get_title(),
                session.user.title if session.user else None
            ))
            session.skip = True

        # Ensure we are only scrobbling for the client listed in preferences
        if not self.valid_client(session):
            Log.Info('Ignoring item [%s](%s) played by other client: %s' % (
                session_key,
                session.get_title(),
                session.client.name if session.client else None
            ))
            session.skip = True

        if session.skip:
            session.save()
            return

        media_type = session.get_type()

        # Check if we are scrobbling a known media type
        if not media_type:
            Log.Info('Playing unknown item, will not be scrobbled: "%s"' % session.get_title())
            session.skip = True
            return

        # Calculate progress
        session.progress = int(round((float(view_offset) / (session.metadata['duration'] * 60 * 1000)) * 100, 0))

        action = self.get_action(session, state)

        if state == 'playing':
            session.paused_since = None

        # No action needed, exit
        if not action:
            Log.Debug('Nothing to do this time for ' + session.get_title())
            session.save()
            return

        if self.handle_action(session, media_type, action, state):
            Dict.Save()
