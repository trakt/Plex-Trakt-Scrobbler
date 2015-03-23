from core.action import ActionHelper
from core.helpers import try_convert, get_filter
from core.logger import Logger
from data.watch_session import WatchSession

from expiringdict import ExpiringDict
from plex.objects.library.metadata.episode import Episode
from plex.objects.library.metadata.movie import Movie
from plex.objects.library.metadata.season import Season
from plex_activity import Activity
from plex_metadata import Metadata, Guid, Matcher
from Queue import PriorityQueue
from threading import Thread
from trakt import Trakt

log = Logger('pts.action_manager')

PRIORITY_EVENT = 20
PRIORITY_SCROBBLE = 10

MAX_RETRIES = 3


class ActionManager(object):
    pending = PriorityQueue()
    history = ExpiringDict(100000, 600)

    thread = None

    @classmethod
    def initialize(cls):
        cls.thread = Thread(target=cls.process)

        Activity.on('logging.action.played', cls.on_played)\
                .on('logging.action.unplayed', cls.on_unplayed)

        WatchSession.configure(cls)

    #
    # Event handlers
    #

    @classmethod
    def on_played(cls, info):
        if not Prefs['sync_instant_actions']:
            log.debug('"Instant Actions" not enabled, ignoring')
            return

        cls.queue_event('add', info)

    @classmethod
    def on_unplayed(cls, info):
        if not Prefs['sync_instant_actions']:
            log.debug('"Instant Actions" not enabled, ignoring')
            return

        cls.queue_event('remove', info)

    #
    # Queue
    #

    @classmethod
    def build_key(cls, rating_key, cur_episode=None, identifier=None):
        if not identifier or len(identifier) != 2:
            return rating_key

        _, episodes = identifier

        if len(episodes) < 2 or cur_episode >= len(episodes):
            return rating_key

        return '%s:%s' % (
            rating_key,
            cur_episode
        )

    @classmethod
    def queue_event(cls, action, info, priority=PRIORITY_EVENT, callback=None):
        return cls.queue(
            {
                'type': 'event',
                'key': info.get('rating_key'),

                'kwargs': {
                    'action': action,
                    'info': info
                }
            },
            priority, callback
        )

    @classmethod
    def queue_scrobble(cls, key, action, request, priority=PRIORITY_SCROBBLE, callback=None):
        return cls.queue(
            {
                'type': 'scrobble',
                'key': key,

                'kwargs': {
                    'action': action,
                    'request': request
                }
            },
            priority, callback
        )

    @classmethod
    def queue(cls, item, priority=30, callback=None):
        if not cls.can_retry(item, priority):
            log.info('Maximum retires exceeded for: %r (priority: %s)', item, priority)
            return False

        # Store in queue
        cls.pending.put((priority, item, callback))

        log.debug('Queued %s: %s (priority: %s)', item.get('type'), item, priority)
        return True

    @classmethod
    def can_retry(cls, item, priority):
        type = item.get('type')

        if type == 'event' and PRIORITY_EVENT - priority < MAX_RETRIES:
            return True

        if type == 'scrobble' and PRIORITY_SCROBBLE - priority < MAX_RETRIES:
            return True

        return False

    #
    # Process events
    #

    @classmethod
    def start(cls):
        cls.thread.start()

    @classmethod
    def process(cls):
        while True:
            priority, item, callback = cls.pending.get()

            try:
                cls.send(priority, item, callback)
            except Exception, ex:
                log.warn('Unable to send action - %s', ex, exc_info=True)

    #
    # Send actions/events
    #

    @classmethod
    def update_history(cls, key, performed=None, sent=None):
        history = cls.history.get(key, {'performed': [], 'sent': []})

        if performed == 'start':
            if history['performed'] or history['sent']:
                log.debug('History for "%s" reset, new session started', key)

            # Reset history
            history['performed'] = []
            history['sent'] = []

        # Update history
        if performed:
            history['performed'].append(performed)

        if sent:
            history['sent'].append(sent)

        # Ensure item is stored in history
        cls.history[key] = history

    @classmethod
    def guess_performed(cls, item):
        # Retrieve request details
        kwargs = item.get('kwargs', {})

        action = kwargs.get('action')
        request = kwargs.get('request')

        if not action or not request:
            log.warn('Missing "action" or "request" parameter in request')
            return None

        if action in ['add', 'remove', 'start', 'pause']:
            return action

        if action == 'stop':
            progress = request.get('progress')

            if progress is None:
                log.warn('Missing "progress" parameter in request')
                return None

            if progress < 80:
                return 'pause'
            else:
                return 'scrobble'

        return None

    @classmethod
    def send(cls, priority, item, callback):
        type = item.get('type', None)

        if type is None:
            log.warn('Missing type for: %r', item)
            return False

        func = getattr(cls, 'send_%s' % type, None)

        if func is None:
            log.warn('Unknown type "%s" for: %s', type, item)
            return False

        # Check action against history
        history = cls.history.get(item['key'], {})

        if not cls.valid_request(item, history):
            return False

        # Execute request
        kwargs = item.get('kwargs', {})

        log.debug('[%s] Sending action (kwargs: %r)', item['key'], kwargs)

        performed, response = func(**kwargs)

        #
        # NOTE: disabled request retrying to avoid duplicate scrobbles
        #
        # if response is None:
        #     # Request failed, retry the request
        #     queued = cls.queue(
        #         item,
        #         priority=priority - 1,
        #         callback=callback
        #     )
        #
        #     if queued:
        #         # Request is being retried, don't fire callback yet
        #         return

        # Guess `performed` action if there was a error
        if not performed:
            performed = cls.guess_performed(item)

            if performed:
                log.debug('[%s] Request returned an error, assuming action performed was %r', item['key'], performed)
            else:
                log.debug('[%s] Request returned an error, unable to guess performed action', item['key'])

        # Store action in history
        if performed:
            log.debug('[%s] Action sent (performed: %r, response: %r)', item['key'], performed, response)

            cls.update_history(item['key'], performed, kwargs.get('action'))

        # Fire callback (if one exists)
        if not callback:
            return True

        try:
            callback(performed, priority, item)
        except Exception, ex:
            log.warn('Exception raised in action callback: %s', ex, exc_info=True)

        return True

    @classmethod
    def send_event(cls, action, info):
        request = cls.from_event(info)

        if request is None:
            log.warn("send_event - couldn't build request, unable to send the action")

        if not request:
            return None, False

        func = getattr(Trakt['sync/history'], action, None)

        if not func:
            log.warn('send_event - unknown action "%s"', action)
            return None, False

        try:
            response = func(request)
        except Exception, ex:
            return None, None

        if not response:
            return None, response

        if action == 'add':
            # Translate "add" -> "scrobble"
            action = 'scrobble'

        return action, response

    @classmethod
    def send_scrobble(cls, action, request):
        try:
            response = Trakt['scrobble'].action(action, **request)
        except Exception, ex:
            return None, None

        if not response:
            return None, response

        return response.get('action'), response

    #
    # Action Validation
    #

    @classmethod
    def is_scrobbled(cls, performed):
        for action in reversed(performed):
            if action == 'scrobble':
                return True

            if action == 'remove':
                return False

        return False

    @classmethod
    def valid_request(cls, item, history):
        # Retrieve request details
        kwargs = item.get('kwargs', {})
        action = kwargs.get('action')

        if not action:
            log.warn('Missing "action" parameter in request')
            return False

        return cls.valid_action(action, history)

    @classmethod
    def valid_action(cls, action, history):
        # Retrieve history details
        performed = history.get('performed', [])
        sent = history.get('sent', [])

        if sent and sent[-1] == action:
            log.info('Ignoring duplicate "%s" action (history: %s)', action, history)
            return False

        if action in ['add', 'stop'] and cls.is_scrobbled(performed):
            log.info('Item already scrobbled, ignoring "%s" action (history: %s)', action, history)
            return False

        return True

    #
    # Request builders
    #

    @classmethod
    def from_event(cls, info):
        account_key = try_convert(info.get('account_key'), int)
        rating_key = info.get('rating_key')

        if account_key is None or rating_key is None:
            log.warn('Invalid action format: %s', info)
            return None

        if account_key != 1:
            log.debug('Ignoring action from shared account')
            return None

        if WatchSession.is_active(rating_key, lambda ws: not ws.update_required):
            log.debug('Ignoring action, item is currently being watched')
            return False

        metadata = Metadata.get(rating_key)

        if not metadata:
            log.debug('Ignoring action, unable to retrieve metadata')
            return False

        section = metadata.section.title.lower()

        f_allow, _ = get_filter('filter_sections')

        if f_allow is not None and section not in f_allow:
            log.debug('Ignoring action, section has been filtered')
            return False

        guid = Guid.parse(metadata.guid)

        request = {}

        if type(metadata) is Movie:
            request = cls.from_movie(metadata, guid)
        elif type(metadata) is Season:
            request = cls.from_season(metadata, guid)
        elif type(metadata) is Episode:
            request = cls.from_episode(metadata, guid)
        else:
            log.warn('Unsupported metadata type: %r', metadata)
            return None

        log.debug('request: %r', request)

        return request

    @classmethod
    def from_movie(cls, movie, guid):
        # Set identifier
        movie = ActionHelper.set_identifier({}, guid)

        if not movie:
            # Couldn't find a valid identifier
            return None

        return {
            'movies': [movie]
        }

    @classmethod
    def from_season(cls, season, guid):
        # Build request
        show = {
            'seasons': [
                {
                    'number': season.index,
                    'episodes': ActionHelper.trakt.episodes(season.children())
                }
            ]
        }

        # Set identifier
        show = ActionHelper.set_identifier(show, guid)

        if not show:
            # Couldn't find a valid identifier
            return None

        return {
            'shows': [show]
        }

    @classmethod
    def from_episode(cls, episode, guid):
        # Build request
        show = {
            'seasons': [
                {
                    'number': episode.season.index,
                    'episodes': ActionHelper.trakt.episodes([episode])
                }
            ]
        }

        # Set identifier
        show = ActionHelper.set_identifier(show, guid)

        if not show:
            # Couldn't find a valid identifier
            return None

        return {
            'shows': [show]
        }
