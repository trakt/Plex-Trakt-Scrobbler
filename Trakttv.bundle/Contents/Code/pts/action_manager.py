from core.action import ActionHelper
from core.logger import Logger

from plex.objects.library.metadata.episode import Episode
from plex.objects.library.metadata.movie import Movie
from plex_activity import Activity
from plex_metadata import Metadata, Guid, Matcher
from trakt import Trakt

log = Logger('pts.action_manager')


class ActionManager(object):
    @classmethod
    def initialize(cls):
        Activity.on('logging.action.played', cls.on_played)\
                .on('logging.action.unplayed', cls.on_unplayed)

    @classmethod
    def on_played(cls, info):
        log.debug('on_played - %s', info)

        cls.send('seen', info['rating_key'])

    @classmethod
    def on_unplayed(cls, info):
        log.debug('on_unplayed - %s', info)

        cls.send('unseen', info['rating_key'])

    @classmethod
    def send(cls, action, rating_key):
        metadata = Metadata.get(rating_key)
        guid = Guid.parse(metadata.guid)

        path, request = None, None

        if type(metadata) is Movie:
            path, request = cls.build_movie(metadata, guid)
        elif type(metadata) is Episode:
            path, request = cls.build_episode(metadata, guid)

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
    def build_movie(cls, metadata, guid):
        return 'movie', {}

    @classmethod
    def build_episode(cls, metadata, guid):
        request = ActionHelper.plex.to_trakt(
            (guid.agent, guid.sid),
            metadata.show,
            guid=guid,
            year=metadata.year
        )

        request['episodes'] = []

        season, episodes = Matcher.process(metadata)

        for episode in episodes:
            request['episodes'].append(ActionHelper.plex.to_trakt(
                (season, episode),
                metadata,
                include_identifier=False
            ))

        return 'show/episode', request
