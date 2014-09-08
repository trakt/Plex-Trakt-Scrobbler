from core.helpers import str_pad, get_filter, get_pref, normalize, any
from core.logger import Logger
from core.method_manager import Method, Manager

from plex_metadata import Metadata
from trakt import Trakt
import ipaddress
import math

log = Logger('pts.scrobbler')


class ScrobblerMethod(Method):
    def __init__(self):
        super(ScrobblerMethod, self).__init__(threaded=False)

    @staticmethod
    def status_message(ws, state):
        state = state[:2].upper() if state else '?'
        progress = ws.progress if ws.progress is not None else '?'

        status = '[%s%s]' % (
            str_pad(state, 2, trim=True),
            str_pad(progress, 3, 'right', trim=True)
        )

        metadata_key = None

        if ws.metadata and ws.guid:
            metadata_key = (ws.guid.agent, ws.guid.sid)

            if type(metadata_key) is tuple:
                metadata_key = ', '.join(repr(x) for x in metadata_key)

        title = '%s (%s)' % (ws.title, metadata_key)

        def build(message_format):
            return '%s %s' % (status, message_format % title)

        return build

    def get_action(self, session, state):
        """
        :type session: WatchSession
        :type state: str

        :rtype: str or None
        """

        status_message = self.status_message(session, state)

        # State has changed
        if state not in [session.cur_state, 'buffering']:
            session.cur_state = state

            if state == 'stopped' and session.watching:
                log.info(status_message('%s stopped, watching status cancelled'))
                session.watching = False
                return 'cancelwatching'

            if state == 'paused' and not session.paused_since:
                log.info(status_message("%s just paused, waiting 15s before cancelling the watching status"))

                session.paused_since = Datetime.Now()
                return None

            if state == 'playing' and not session.watching:
                log.info(status_message('Sending watch status for %s'))
                session.watching = True
                return 'watching'

        elif state == 'playing':
            # scrobble item
            if not session.scrobbled and session.progress >= get_pref('scrobble_percentage'):
                log.info(status_message('Scrobbling %s'))
                return 'scrobble'

            # update every 10 min if media hasn't finished
            elif session.progress < 100 and (session.last_updated + Datetime.Delta(minutes=10)) < Datetime.Now():
                log.info(status_message('Updating watch status for %s'))
                session.watching = True
                return 'watching'

            # cancel watching status on items at 100% progress
            elif session.progress >= 100 and session.watching:
                log.info(status_message('Media finished, cancelling watching status for %s'))
                session.watching = False
                return 'cancelwatching'

        return None

    @staticmethod
    def get_request_parameters(ws):
        values = {}

        if not ws.type:
            return None

        if ws.type == 'show':
            if not ws.identifier:
                log.warn('Unable to retrieve episode identifier')
                return None

            season, episodes = ws.identifier

            if ws.cur_episode >= len(episodes):
                log.warn('Unable to find episode at index %s, available episodes: %s', ws.cur_episode, ws.metadata['episodes'])
                return None

            values.update({
                'season': season,
                'episode': episodes[ws.cur_episode],

                # Scale duration to number of episodes
                'duration': ws.metadata['duration'] / len(episodes)
            })
        else:
            values['duration'] = ws.metadata['duration']

        # Add TVDB/TMDB identifier
        values = PlexMetadata.add_identifier(values, ws.metadata)

        values.update({
            'progress': ws.progress,
            'title': ws.title
        })

        if 'year' in ws.metadata:
            values['year'] = ws.metadata['year']

        return values

    @classmethod
    def handle_state(cls, session, state):
        if state == 'playing' and session.paused_since:
            session.paused_since = None
            #session.save()
            return True

        # If stopped, delete the session
        if state == 'stopped':
            log.debug(session.title + ' stopped, deleting the session')
            session.delete()
            return True

        # If paused, queue a session update when playing begins again
        if state == 'paused' and not session.update_required:
            log.debug(session.title + ' paused, session update queued to run when resumed')
            session.update_required = True
            #session.save()
            return True

        return False

    @classmethod
    def handle_action(cls, session, media, action, state):
        # Setup Data to send to trakt
        parameters = cls.get_request_parameters(session)
        if not parameters:
            log.info('Invalid parameters, unable to continue')
            return False

        log.trace('Sending action "%s/%s"', media, action)

        if action in ['watching', 'scrobble']:
            response = Trakt[media][action](**parameters)
        else:
            response = Trakt[media][action]()

        if not response or response.get('status') != 'success':
            log.warn('Unable to send scrobbler action')

        session.last_updated = Datetime.Now()

        if action == 'scrobble':
            session.scrobbled = True

            # If just scrobbled, force update on next status update to set as watching again
            session.last_updated = Datetime.Now() - Datetime.Delta(minutes=20)

        #session.save()

    @staticmethod
    def offset_jumped(session, current):
        duration = session.metadata['duration'] * 60 * 1000

        last = session.last_view_offset

        if last is None:
            return False

        perc_current = (float(current) / duration) * 100
        perc_last = (float(last) / duration) * 100

        perc_change = perc_current - perc_last

        log.trace(
            'Checking for offset jump - last: %s (%s), current: %s (%s), change: %s',
            last, perc_last, current, perc_current,
            perc_change
        )

        if perc_change > 98:
            log.debug('View offset jumped by %.02f%%', perc_change)
            return True

        return False

    @staticmethod
    def update_progress(ws, view_offset):
        if not ws or not ws.metadata:
            log.warn('Invalid session/metadata')
            return False

        # Ensure duration is positive
        if not ws.metadata.duration or ws.metadata.duration <= 0:
            log.warn('Invalid duration')
            return False

        duration = ws.metadata.duration * 60 * 1000

        total_progress = float(view_offset) / duration

        if ws.type == 'show':
            if not ws.identifier:
                log.warn('Unable to retrieve episode identifier')
                return None

            season, episodes = ws.identifier

            cur_episode = int(math.floor(len(episodes) * total_progress))

            # If episode has changed, reset the state to start new session
            if cur_episode != ws.cur_episode and ws.cur_episode is not None:
                log.info('Session has changed episodes, state has been reset')
                ws.reset()

            ws.cur_episode = cur_episode

            # Scale progress based on number of episodes
            total_progress = (len(episodes) * total_progress) - ws.cur_episode

        ws.progress = int(round(total_progress * 100, 0))
        return True

    def valid(self, session):
        filtered = None

        # Check filters
        if not self.valid_user(session) or \
           not self.valid_client(session) or \
           not self.valid_section(session): #or\
           # TODO not self.valid_address(session):
            filtered = True
        else:
            filtered = False

        if session.filtered != filtered:
            # value changed, update session
            session.filtered = filtered
            #session.save()

        return not filtered

    @staticmethod
    def match(session, key, f_current, f_validate, f_check=None, f_transform=None, normalize_values=True):
        if Prefs[key] is None:
            return True

        if f_check and f_check():
            return True

        value = f_current()

        # Normalize value
        if normalize_values:
            if value:
                value = value.strip()

            value = normalize(value)

        # Fetch filter
        f_allow, f_deny = get_filter(key, normalize_values=normalize_values)

        # Wildcard
        if f_allow is None and f_deny is None:
            return True

        if f_transform:
            # Transform filter values
            f_allow = [f_transform(x) for x in f_allow]
            f_deny = [f_transform(x) for x in f_deny]

        log.trace('validate "%s" - value: %s, allow: %s, deny: %s', key, repr(value), f_allow, f_deny)

        if f_validate(value, f_allow, f_deny):
            log.info('Ignoring item [%s](%s) played by filtered "%s": %s' % (
                session.item_key,
                session.title,
                key, repr(f_current())
            ))
            return False

        return True

    @classmethod
    def valid_user(cls, ws):
        return cls.match(
            ws, 'scrobble_names',
            f_current=lambda: ws.session.user.title if ws.session.user else None,
            f_validate=lambda value, f_allow, f_deny: (
                (f_allow and (
                    not ws.session.user or
                    value not in f_allow
                )) or
                value in f_deny
            )
        )

    @classmethod
    def valid_client(cls, ws):
        return cls.match(
            ws, 'scrobble_clients',
            f_current=lambda: ws.session.client.name if ws.session.client else None,
            f_validate=lambda value, f_allow, f_deny: (
                (f_allow and (
                    not ws.session.client or
                    value not in f_allow
                )) or
                value in f_deny
            )
        )

    @classmethod
    def valid_section(cls, ws):
        return cls.match(
            ws, 'filter_sections',
            f_current=lambda: ws.metadata.section.title,
            f_validate=lambda value, f_allow, f_deny: (
                (f_allow and value not in f_allow) or
                value in f_deny
            ),
            f_check=lambda: (
                not ws.metadata or
                not ws.metadata.section.title
            )
        )

    @classmethod
    def valid_address(cls, ws):
        def f_current():
            if not ws.session.client or not ws.session.client.address:
                return None

            value = ws.session.client.address

            try:
                return ipaddress.ip_address(unicode(value))
            except ValueError, ex:
                log.warn('validate "filter_networks" - unable to parse IP Address: %s', repr(value))
                return None

        def f_validate(value, f_allow, f_deny):
            if not value:
                return True

            allowed = any([
                value in network
                for network in f_allow
                if network is not None
            ])

            denied = any([
                value in network
                for network in f_deny
                if network is not None
            ])

            return not allowed or denied

        def f_transform(value):
            if not value:
                return None

            try:
                return ipaddress.ip_network(unicode(value))
            except ValueError, ex:
                log.warn('validate "filter_networks" - unable to parse IP Network: %s', repr(value))
                return None

        return cls.match(
            ws, 'filter_networks',
            normalize_values=False,
            f_current=f_current,
            f_validate=f_validate,
            f_transform=f_transform
        )


class Scrobbler(Manager):
    tag = 'pts.scrobbler'

    available = []
    enabled = []
