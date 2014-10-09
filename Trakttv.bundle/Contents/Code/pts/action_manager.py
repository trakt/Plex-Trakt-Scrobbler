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

        cls.pending.put(('seen', info))

        log.debug('"seen" action queued: %s', info)

    @classmethod
    def on_unplayed(cls, info):
        if not Prefs['sync_instant_actions']:
            log.debug('"Instant Actions" not enabled, ignoring')
            return

        cls.pending.put(('unseen', info))

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
    def send(cls, action, info):
        account_key = try_convert(info.get('account_key'), int)
        rating_key = info.get('rating_key')

        if account_key is None or rating_key is None:
            log.warn('Invalid "%s" action format', action)
            return

        if account_key != 1:
            log.debug('Ignoring action from shared account')
            return

        metadata = Metadata.get(rating_key)
        guid = Guid.parse(metadata.guid)

        path, request = None, None

        if type(metadata) is Movie:
            path, request = cls.request_movie(metadata, guid)

        if type(metadata) is Season:
            path, request = cls.request_season(metadata, guid)

        if type(metadata) is Episode:
            path, request = cls.request_episode(metadata, guid)

        if not path or not request:
            log.warn('Unsupported metadata type: %r', metadata)
            return

        log.debug('request: %r', request)

        response = Trakt[path][action](**request)

        if response is None:
            # Request failed (rejected unmatched media, etc..)
            return

        log.debug('response: %r', response)

    @classmethod
    def request_movie(cls, movie, guid):
        return 'movie', {'movies': [
            ActionHelper.plex.to_trakt(
                (guid.agent, guid.sid),
                movie,
                guid=guid
            )
        ]}

    @classmethod
    def request_season(cls, season, guid):
        request = ActionHelper.plex.to_trakt(
            (guid.agent, guid.sid),
            season.show,
            guid=guid,
            year=season.year
        )

        request['episodes'] = []

        for episode in season.children():
            request['episodes'].extend(cls.from_episode(episode))

        return 'show/episode', request

    @classmethod
    def request_episode(cls, episode, guid):
        request = ActionHelper.plex.to_trakt(
            (guid.agent, guid.sid),
            episode.show,
            guid=guid,
            year=episode.year
        )

        request['episodes'] = cls.from_episode(episode)

        return 'show/episode', request

    @classmethod
    def from_episode(cls, episode):
        result = []

        season_num, episodes = Matcher.process(episode)

        for episode_num in episodes:
            result.append(ActionHelper.plex.to_trakt(
                (season_num, episode_num),
                episode,
                include_identifier=False
            ))

        return result
