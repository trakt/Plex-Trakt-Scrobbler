from core.trakt import Trakt


class Scrobbler(object):
    @staticmethod
    def get_status_label(session, state):
        return '[{0:<2}{1:>3}]'.format(
            state[:2].upper() if state else '?',
            session.progress if session and session.progress is not None else '?'
        )

    def get_action(self, session, state):
        """
        :type session: WatchSession
        :type state: str

        :rtype: str or None
        """

        status_label = self.get_status_label(session, state)

        # State has changed
        if state not in [session.cur_state, 'buffering']:
            session.cur_state = state

            if state == 'stopped' and session.watching:
                Log.Debug('%s %s stopped, watching status cancelled' % (
                    status_label, session.get_title()
                ))
                session.watching = False
                return 'cancelwatching'

            if state == 'paused' and not session.paused_since:
                Log.Debug("%s %s just paused, waiting 15s before cancelling the watching status" % (
                    status_label, session.get_title()
                ))

                session.paused_since = Datetime.Now()
                return None

            if state == 'playing' and not session.watching:
                Log.Debug('%s Sending watch status for %s' % (status_label, session.get_title()))
                session.watching = True
                return 'watching'

        elif state == 'playing':
            # scrobble item
            if not session.scrobbled and session.progress >= 80:
                Log.Debug('%s Scrobbling %s' % (status_label, session.get_title()))
                return 'scrobble'

            # update every 10 min if media hasn't finished
            elif session.progress < 100 and (session.last_updated + Datetime.Delta(minutes=10)) < Datetime.Now():
                Log.Debug('%s Updating watch status for %s' % (status_label, session.get_title()))
                session.watching = True
                return 'watching'

            # cancel watching status on items at 100% progress
            elif session.progress >= 100 and session.watching:
                Log.Debug('%s Media finished, cancelling watching status for %s' % (
                    status_label,
                    session.get_title()
                ))
                session.watching = False
                return 'cancelwatching'

        return None

    @staticmethod
    def get_request_parameters(session):
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

    @classmethod
    def handle_state(cls, session, state):
        if state == 'playing' and session.paused_since:
            session.paused_since = None
            return True

        # If stopped, delete the session
        if state == 'stopped':
            Log.Debug(session.get_title() + ' stopped, deleting the session')
            session.delete()
            return True

        # If paused, queue a session update when playing begins again
        if state == 'paused' and not session.update_required:
            Log.Debug(session.get_title() + ' paused, session update queued to run when resumed')
            session.update_required = True
            return True

        return False

    @classmethod
    def handle_action(cls, session, media_type, action, state):
        # Setup Data to send to Trakt
        parameters = cls.get_request_parameters(session)
        if not parameters:
            Log.Info('Invalid parameters, unable to continue')
            return False

        response = Trakt.Media.action(media_type, action, **parameters)
        if not response['success']:
            Log.Warn('Unable to send scrobbler action')

        session.last_updated = Datetime.Now()

        if action == 'scrobble':
            session.scrobbled = True

            # If just scrobbled, force update on next status update to set as watching again
            session.last_updated = Datetime.Now() - Datetime.Delta(minutes=20)

        session.save()

    @staticmethod
    def update_progress(session, view_offset):
        if not session or not session.metadata:
            return False

        # Ensure duration is positive
        if session.metadata.get('duration', 0) <= 0:
            return False

        duration_millis = session.metadata['duration'] * 60 * 1000
        perc_float = float(view_offset) / duration_millis

        session.progress = int(round(perc_float * 100, 0))

        return True

    @staticmethod
    def valid_user(session):
        if Prefs['scrobble_names'] is None:
            return True

        return session.user and Prefs['scrobble_names'].lower() == session.user.title.lower()

    @staticmethod
    def valid_client(session):
        if Prefs['scrobble_clients'] is None:
            return True

        clients = [x.strip().lower() for x in Prefs['scrobble_clients'].split(',')]

        return session.client and session.client.name.lower() in clients
