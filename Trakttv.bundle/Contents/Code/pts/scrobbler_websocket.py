from core.pms import PMS
from pts.scrobbler import Scrobbler
from core.trakt import Trakt
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

        session = WatchSession.from_section(video_section, state)
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

    def get_action(self, session, state):
        """
        :type session: WatchSession
        :type state: str

        :rtype: str or None
        """

        if state not in [session.cur_state, 'buffering']:
            if state in 'stopped':
                Log.Debug(session.get_title() + ' stopped, watching status cancelled')
                return 'cancelwatching'

            if state == 'paused':
                if not session.paused_since:
                    Log.Debug(session.get_title() + " just paused, waiting 15s before cancelling the watching status")
                    session.paused_since = Datetime.Now()
                    return None

                if Datetime.Now() > session.paused_since + Datetime.Delta(seconds=15):
                    Log.Debug(session.get_title() + " paused for 15s, watching status cancelled")
                    return 'cancelwatching'

            if state == 'playing':
                Log.Debug('Updating watch status for ' + session.get_title())
                return 'watching'

        #scrobble item
        elif state == 'playing' and not session.scrobbled and session.progress > 80:
            Log.Debug('Scrobbling ' + session.get_title())
            return 'scrobble'

        # update every 10 min
        elif state == 'playing' and ((session.last_updated + Datetime.Delta(minutes=10)) < Datetime.Now()):
            Log.Debug('Updating watch status for ' + session.get_title())
            return 'watching'

        return None

    def get_request_parameters(self, session):
        values = {}

        session_type = session.get_type()
        if not session_type:
            return None

        if session_type == 'show':
            values.update({
                'tvdb_id': session.metadata['tvdb_id'],
                'season': session.metadata['season'],
                'episode': session.metadata['episode']
            })

        if session_type == 'movie':
            if session.metadata['imdb_id']:
                values['imdb_id'] = session.metadata['imdb_id']
            elif session.metadata['tmdb_id']:
                values['tmdb_id'] = session.metadata['tmdb_id']

        values.update({
            'duration': session.metadata['duration'],
            'progress': session.progress,
            'title': session.get_title()
        })

        if 'year' in session.metadata:
            values['year'] = session.metadata['year']

        return values

    def update(self, session_key, state, view_offset):
        session = self.get_session(session_key, state, view_offset)
        if not session:
            Log.Info('Invalid session, unable to continue')
            return

        # Ensure we are only scrobbling for the myPlex user listed in preferences
        if (Prefs['scrobble_names'] is not None) and (Prefs['scrobble_names'] != session.user.title):
            Log.Info('Ignoring item (' + session.get_title() + ') played by other user: ' + session.user.title)
            session.skip = True
            return

        media_type = session.get_type()

        # Check if we are scrobbling a known media type
        if not media_type:
            Log.Info('Playing unknown item, will not be scrobbled: ' + session.get_title())
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

        # Setup Data to send to Trakt
        parameters = self.get_request_parameters(session)
        if not parameters:
            Log.Info('Invalid parameters, unable to continue')
            return

        Trakt.Media.action(media_type, action, **parameters)

        if action == 'scrobble':
            session.scrobbled = True

            # If just scrobbled, force update on next status update to set as watching again
            session.last_updated = Datetime.Now() - Datetime.Delta(minutes=20)

        session.cur_state = state
        session.last_updated = Datetime.Now()

        # If stopped, delete the session
        if state == 'stopped':
            Log.Debug(session.get_title() + ' stopped, deleting the session')
            session.delete()
            Dict.Save()
            return

        # If paused, queue a session update when playing begins again
        if state == 'paused':
            Log.Debug(session.get_title() + ' paused, session update queued to run when resumed')
            session.update_required = True

        session.save()
        Dict.Save()
