from core.trakt import Trakt


class Scrobbler(object):
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
            if session.metadata.get('imdb_id'):
                values['imdb_id'] = session.metadata['imdb_id']
            elif session.metadata.get('tmdb_id'):
                values['tmdb_id'] = session.metadata['tmdb_id']

        values.update({
            'duration': session.metadata['duration'],
            'progress': session.progress,
            'title': session.get_title()
        })

        if 'year' in session.metadata:
            values['year'] = session.metadata['year']

        return values

    def handle_action(self, session, media_type, action, state):
        # Setup Data to send to Trakt
        parameters = self.get_request_parameters(session)
        if not parameters:
            Log.Info('Invalid parameters, unable to continue')
            return False

        Trakt.Media.action(media_type, action, **parameters)

        session.cur_state = state
        session.last_updated = Datetime.Now()

        if action == 'scrobble':
            session.scrobbled = True

            # If just scrobbled, force update on next status update to set as watching again
            session.last_updated = Datetime.Now() - Datetime.Delta(minutes=20)

        # If stopped, delete the session
        if state == 'stopped':
            Log.Debug(session.get_title() + ' stopped, deleting the session')
            session.delete()
            return True

        # If paused, queue a session update when playing begins again
        if state == 'paused':
            Log.Debug(session.get_title() + ' paused, session update queued to run when resumed')
            session.update_required = True

        session.save()

    def valid_user(self, session):
        if Prefs['scrobble_names'] is None:
            return True

        return session.user and Prefs['scrobble_names'].lower() == session.user.title.lower()

    def valid_client(self, session):
        if Prefs['scrobble_clients'] is None:
            return True

        clients = [x.strip().lower() for x in Prefs['scrobble_clients'].split(',')]

        return session.client and session.client.name.lower() in clients
