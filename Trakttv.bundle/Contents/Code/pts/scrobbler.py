from core.helpers import str_pad, get_filter, get_pref
from core.logger import Logger
from core.method_manager import Method, Manager
from core.trakt import Trakt
from plex.plex_metadata import PlexMetadata
import math

log = Logger('pts.scrobbler')


class ScrobblerMethod(Method):
    def __init__(self):
        super(ScrobblerMethod, self).__init__(threaded=False)

    @staticmethod
    def get_status_label(progress, state):
        return '[%s%s]' % (
            str_pad(state[:2].upper() if state else '?', 2, trim=True),
            str_pad(progress if progress is not None else '?', 3, 'right', trim=True)
        )

    def get_action(self, session, state):
        """
        :type session: WatchSession
        :type state: str

        :rtype: str or None
        """

        status_label = self.get_status_label(session.progress, state)

        # State has changed
        if state not in [session.cur_state, 'buffering']:
            session.cur_state = state

            if state == 'stopped' and session.watching:
                log.info('%s %s stopped, watching status cancelled' % (
                    status_label, session.get_title()
                ))
                session.watching = False
                return 'cancelwatching'

            if state == 'paused' and not session.paused_since:
                log.info("%s %s just paused, waiting 15s before cancelling the watching status" % (
                    status_label, session.get_title()
                ))

                session.paused_since = Datetime.Now()
                return None

            if state == 'playing' and not session.watching:
                log.info('%s Sending watch status for %s' % (status_label, session.get_title()))
                session.watching = True
                return 'watching'

        elif state == 'playing':
            # scrobble item
            if not session.scrobbled and session.progress >= get_pref('scrobble_percentage'):
                log.info('%s Scrobbling %s' % (status_label, session.get_title()))
                return 'scrobble'

            # update every 10 min if media hasn't finished
            elif session.progress < 100 and (session.last_updated + Datetime.Delta(minutes=10)) < Datetime.Now():
                log.info('%s Updating watch status for %s' % (status_label, session.get_title()))
                session.watching = True
                return 'watching'

            # cancel watching status on items at 100% progress
            elif session.progress >= 100 and session.watching:
                log.info('%s Media finished, cancelling watching status for %s' % (
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
            if not session.metadata.get('episodes'):
                log.warn('No episodes found in metadata')
                return None

            if session.cur_episode >= len(session.metadata['episodes']):
                log.warn('Unable to find episode at index %s, available episodes: %s', session.cur_episode, session.metadata['episodes'])
                return None

            values.update({
                'season': session.metadata['season'],
                'episode': session.metadata['episodes'][session.cur_episode],

                # Scale duration to number of episodes
                'duration': session.metadata['duration'] / len(session.metadata['episodes'])
            })
        else:
            values['duration'] = session.metadata['duration']

        # Add TVDB/TMDB identifier
        values = PlexMetadata.add_identifier(values, session.metadata)

        values.update({
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
            log.debug(session.get_title() + ' stopped, deleting the session')
            session.delete()
            return True

        # If paused, queue a session update when playing begins again
        if state == 'paused' and not session.update_required:
            log.debug(session.get_title() + ' paused, session update queued to run when resumed')
            session.update_required = True
            return True

        return False

    @classmethod
    def handle_action(cls, session, media_type, action, state):
        # Setup Data to send to Trakt
        parameters = cls.get_request_parameters(session)
        if not parameters:
            log.info('Invalid parameters, unable to continue')
            return False

        response = Trakt.Media.action(media_type, action, **parameters)
        if not response['success']:
            log.warn('Unable to send scrobbler action')

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

        media = session.get_type()
        duration = session.metadata['duration'] * 60 * 1000

        total_progress = float(view_offset) / duration

        if media == 'show':
            if 'episodes' not in session.metadata:
                return False

            cur_episode = int(math.floor(len(session.metadata['episodes']) * total_progress))

            # If episode has changed, reset the state to start new session
            if cur_episode != session.cur_episode and session.cur_episode is not None:
                log.info('Session has changed episodes, state has been reset')
                session.reset()

            session.cur_episode = cur_episode

            # Scale progress based on number of episodes
            total_progress = (len(session.metadata['episodes']) * total_progress) - session.cur_episode

        session.progress = int(round(total_progress * 100, 0))

        return True

    @staticmethod
    def valid_user(session):
        if Prefs['scrobble_names'] is None:
            return True

        # Normalize username
        username = session.user.title.lower() if session.user else None

        # Fetch filter
        filter = get_filter('scrobble_names')
        if filter is None:
            return True

        log.trace('validate user - username: "%s", filter: %s', username, filter)

        if not session.user or username not in filter:
            log.info('Ignoring item [%s](%s) played by filtered user: %s' % (
                session.item_key,
                session.get_title(),
                session.user.title if session.user else None
            ))
            return False

        return True

    @staticmethod
    def valid_client(session):
        if Prefs['scrobble_clients'] is None:
            return True

        # Normalize client name
        client_name = session.client.name.lower() if session.client else None

        # Fetch filter
        filter = get_filter('scrobble_clients')
        if filter is None:
            return True

        log.trace('validate client - client_name: "%s", filter: %s', client_name, filter)

        if not session.client or client_name not in filter:
            log.info('Ignoring item [%s](%s) played by filtered client: %s' % (
                session.item_key,
                session.get_title(),
                client_name
            ))
            return False

        return True

    @staticmethod
    def valid_section(session):
        title = session.metadata.get('section_title')
        if not title:
            return True

        # Fetch filter
        filter = get_filter('filter_sections')
        if filter is None:
            return True

        # Normalize title
        title = title.strip().lower()

        log.trace('validate section - title: "%s", filter: %s', title, filter)

        # Check section title against filter
        if title not in filter:
            log.info('Ignoring item [%s](%s) played from filtered section "%s"' % (
                session.item_key,
                session.get_title(),
                session.metadata.get('section_title')
            ))
            return False

        return True



class Scrobbler(Manager):
    tag = 'pts.scrobbler'

    available = []
    enabled = []
