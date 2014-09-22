from core.action import ActionHelper
from core.helpers import try_convert
from core.logger import Logger

from plex.objects.library.metadata.episode import Episode
from plex.objects.library.metadata.movie import Movie
from plex.objects.library.metadata.season import Season
from plex_activity import Activity
from plex_metadata import Metadata, Guid, Matcher
from Queue import Queue
from threading import Thread
from trakt import Trakt

log = Logger('pts.action_manager')


class ActionManager(object):
    pending = Queue()
    thread = None

    @classmethod
    def initialize(cls):
        cls.thread = Thread(target=cls.process)

        Activity.on('logging.action.played', cls.on_played)\
                .on('logging.action.unplayed', cls.on_unplayed)

    @classmethod
    def on_played(cls, info):
        if not Prefs['sync_instant_actions']:
            log.debug('"Instant Actions" not enabled, ignoring')
            return

        cls.pending.put((Trakt['sync/history'].add, info))

        log.debug('"seen" action queued: %s', info)

    @classmethod
    def on_unplayed(cls, info):
        if not Prefs['sync_instant_actions']:
            log.debug('"Instant Actions" not enabled, ignoring')
            return

        cls.pending.put((Trakt['sync/history'].remove, info))

        log.debug('"unseen" action queued: %s', info)

    @classmethod
    def start(cls):
        cls.thread.start()

    @classmethod
    def process(cls):
        while True:
            action = cls.pending.get(block=True)

            try:
                cls.send(*action)
            except Exception, ex:
                log.warn('Unable to send action - %s', ex)

    @classmethod
    def send(cls, func, info):
        request = cls.build(info)

        if request is None:
            log.warn("Couldn't build request, unable to send the action")
            return

        response = func(request)

        if response is None:
            # Request failed (rejected unmatched media, etc..)
            return

        log.debug('response: %r', response)

    @classmethod
    def build(cls, info):
        account_key = try_convert(info.get('account_key'), int)
        rating_key = info.get('rating_key')

        if account_key is None or rating_key is None:
            log.warn('Invalid action format: %s', info)
            return

        if account_key != 1:
            log.debug('Ignoring action from shared account')
            return

        metadata = Metadata.get(rating_key)
        guid = Guid.parse(metadata.guid)

        request = {}

        if type(metadata) is Movie:
            request = cls.build_movie(metadata, guid)
        elif type(metadata) is Season:
            request = cls.build_season(metadata, guid)
        elif type(metadata) is Episode:
            request = cls.build_episode(metadata, guid)
        else:
            log.warn('Unsupported metadata type: %r', metadata)
            return

        log.debug('request: %r', request)

        return request

    @classmethod
    def build_movie(cls, movie, guid):
        return {
            'movies': [
                ActionHelper.set_identifier({}, guid)
            ]
        }

    @classmethod
    def build_season(cls, season, guid):
        # Build list of episodes
        episodes = []

        for episode in season.children():
            cls.append_episode(episodes, episode)

        # Build request
        show = {
            'seasons': [
                {
                    'number': season.index,
                    'episodes': episodes
                }
            ]
        }

        return {
            'shows': [
                ActionHelper.set_identifier(show, guid)
            ]
        }

    @classmethod
    def build_episode(cls, episode, guid):
        # Build list of episodes
        episodes = []

        cls.append_episode(episodes, episode)

        # Build request
        show = {
            'seasons': [
                {
                    'number': episode.season.index,
                    'episodes': episodes
                }
            ]
        }

        return {
            'shows': [
                ActionHelper.set_identifier(show, guid)
            ]
        }

    @classmethod
    def append_episode(cls, collection, episode):
        _, episodes = Matcher.process(episode)

        for episode_num in episodes:
            collection.append({
                'number': episode_num
            })
