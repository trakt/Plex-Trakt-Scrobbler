from plex_database.matcher import Default as Matcher
from plex_database.models import *
from plex_metadata.guid import Guid

from peewee import JOIN_LEFT_OUTER
from stash.algorithms.core.prime_context import PrimeContext
import logging

log = logging.getLogger(__name__)


class LibraryBase(object):
    def __init__(self, library=None):
        self._library = library

    @property
    def library(self):
        return self._library or Library

    @property
    def matcher(self):
        return self.library.matcher

    @staticmethod
    def settings_directory(rating):
        result = {}

        if rating is not None:
            result['rating'] = rating

        return result

    @staticmethod
    def settings_video(rating, view_offset, last_viewed_at):
        result = {}

        if rating is not None:
            result['rating'] = rating

        if view_offset is not None:
            result['view_offset'] = view_offset

        if last_viewed_at is not None:
            result['last_viewed_at'] = last_viewed_at

        return result


class MovieLibrary(LibraryBase):
    def __call__(self, sections, account, fields=None):
        # Retrieve `id` from `Account`
        if account and type(account) is Account:
            account = account.id

        # Map `Section` list to ids
        section_ids = [id for (id, ) in sections]

        #  Set defaults for `fields`
        if not fields:
            fields = [
                MetadataItem.id,
                MetadataItem.parent,

                MetadataItem.guid
            ]

            if account:
                fields.extend([
                    MetadataItemSettings.rating,
                    MetadataItemSettings.view_offset,
                    MetadataItemSettings.last_viewed_at
                ])

        # Blue `where()` query
        query = [
            MetadataItem.library_section << section_ids,
            MetadataItem.metadata_type == MetadataItemType.Movie
        ]

        if account:
            query.append(
                (MetadataItemSettings.id >> None) | (MetadataItemSettings.account == account)
            )

            return MetadataItem.select(*fields).join(
                MetadataItemSettings, JOIN_LEFT_OUTER, on=(
                    MetadataItemSettings.guid == MetadataItem.guid
                ).alias('settings')
            ).where(*query)

        return MetadataItem.select(*fields).where(*query)

    def mapped(self, sections, account, parse_guid=False):
        # Retrieve `id` from `Account`
        if account and type(account) is Account:
            account = account.id

        # Retrieve shows
        movies = Library.movies(sections, account, [
            MetadataItem.id,
            MetadataItem.guid,

            MetadataItemSettings.rating,
            MetadataItemSettings.view_offset,
            MetadataItemSettings.last_viewed_at
        ])

        movies = [
            (id, {
                'guid': (guid, None),
                'settings': self.settings_video(rating, view_offset, last_viewed_at)
            })
            for (id, guid, rating, view_offset, last_viewed_at) in movies.tuples().iterator()
        ]

        def movies_iterator():
            for movie_id, movie in movies:
                # Parse `guid` (if enabled, and not already parsed)
                if parse_guid:
                    raw, parsed = movie['guid']

                    if parsed is None:
                        movie['guid'] = (raw, Guid.parse(raw))

                # Pick `guid` based on request (`parse_guid` parameter)
                guid_raw, guid_parsed = movie['guid']
                guid = guid_parsed if parse_guid else guid_raw

                yield movie_id, guid, {
                    'settings': movie['settings']
                }

        return movies_iterator()


class ShowLibrary(LibraryBase):
    def __call__(self, sections, account, fields=None):
        # Retrieve `id` from `Account`
        if account and type(account) is Account:
            account = account.id

        # Map `Section` list to ids
        section_ids = [id for (id, ) in sections]

        #  Set defaults for `fields`
        if not fields:
            fields = [
                MetadataItem.id,
                MetadataItem.parent,

                MetadataItem.guid,
                MetadataItem.index,
                MetadataItem.metadata_type
            ]

            if account:
                fields.extend([
                    MetadataItemSettings.rating
                ])

        # Build `where()` query
        query = [
            MetadataItem.metadata_type == MetadataItemType.Show,
            MetadataItem.library_section << section_ids
        ]

        if account:
            query.append(
                (MetadataItemSettings.id >> None) | (MetadataItemSettings.account == account)
            )

            return MetadataItem.select(*fields).join(
                MetadataItemSettings, JOIN_LEFT_OUTER, (
                    MetadataItemSettings.guid == MetadataItem.guid
                ).alias('settings')
            ).where(*query)

        return MetadataItem.select(*fields).where(*query)


class SeasonLibrary(LibraryBase):
    def __call__(self, sections, account=None, fields=None):
        # Retrieve `id` from `Account`
        if account and type(account) is Account:
            account = account.id

        # Map `Section` list to ids
        section_ids = [id for (id, ) in sections]

        # Set defaults for `fields`
        if not fields:
            fields = [
                MetadataItem.id,
                MetadataItem.index
            ]

            if account:
                fields.extend([
                    MetadataItemSettings.rating
                ])

        # Build `where()` query
        query = [
            MetadataItem.metadata_type == MetadataItemType.Season,
            MetadataItem.library_section << section_ids
        ]

        if account:
            query.append(
                (MetadataItemSettings.id >> None) | (MetadataItemSettings.account == account)
            )

            return MetadataItem.select(*fields).join(
                MetadataItemSettings, JOIN_LEFT_OUTER, (
                    MetadataItemSettings.guid == MetadataItem.guid
                ).alias('settings')
            ).where(*query)

        return MetadataItem.select(*fields).where(*query)


class EpisodeLibrary(LibraryBase):
    def __call__(self, sections, account=None, fields=None):
        # Retrieve `id` from `Account`
        if account and type(account) is Account:
            account = account.id

        # Map `Section` list to ids
        section_ids = [id for (id, ) in sections]

        # Set defaults for `fields`
        if not fields:
            fields = [
                MetadataItem.id,
                MetadataItem.index
            ]

            if account:
                fields.extend([
                    MetadataItemSettings.rating,
                    MetadataItemSettings.view_offset,
                    MetadataItemSettings.last_viewed_at
                ])

        # Build `where()` query
        query = [
            MetadataItem.metadata_type == MetadataItemType.Episode,
            MetadataItem.library_section << section_ids
        ]

        if account:
            query.append(
                (MetadataItemSettings.id >> None) | (MetadataItemSettings.account == account)
            )

            return MetadataItem.select(*fields).join(
                MetadataItemSettings, JOIN_LEFT_OUTER, (
                    MetadataItemSettings.guid == MetadataItem.guid
                ).alias('settings')
            ).where(*query)

        return MetadataItem.select(*fields).where(*query)

    def mapped(self, sections, account=None, parse_guid=False):
        # Retrieve `id` from `Account`
        if account and type(account) is Account:
            account = account.id

        # Retrieve shows
        shows = Library.shows(sections, account, [
            MetadataItem.id,
            MetadataItem.guid,

            MetadataItemSettings.rating
        ])

        shows = dict([
            (id, {'guid': (guid, None), 'settings': self.settings_directory(rating)})
            for (id, guid, rating) in shows.tuples().iterator()
        ])

        # Retrieve seasons
        seasons = Library.seasons(sections, account, [
            MetadataItem.id,
            MetadataItem.index,

            MetadataItemSettings.rating
        ])

        seasons = dict([
            (id, {'index': index, 'settings': self.settings_directory(rating)})
            for (id, index, rating) in seasons.tuples().iterator()
        ])

        # Retrieve episodes
        Season = MetadataItem.alias()
        Episode = MetadataItem.alias()

        episodes = (MetadataItem
                    .select(
                        MetadataItem.id,

                        Season.id,

                        Episode.id,
                        Episode.index,

                        MetadataItemSettings.rating,
                        MetadataItemSettings.view_offset,
                        MetadataItemSettings.last_viewed_at,

                        MediaPart.duration,
                        MediaPart.file
                    )
                    .join(
                        Season, on=(
                            Season.parent == MetadataItem.id
                        ).alias('season')
                    )
                    .join(
                        Episode, on=(
                            Episode.parent == Season.id
                        ).alias('episode')
                    )
                    .join(
                        MetadataItemSettings, JOIN_LEFT_OUTER, on=(
                            MetadataItemSettings.guid == Episode.guid
                        ).alias('settings')
                    )
                    .switch(Episode)
                    .join(
                        MediaItem, on=(
                            MediaItem.metadata_item == Episode.id
                        ).alias('media')
                    )
                    .join(
                        MediaPart, on=(
                            MediaPart.media_item == MediaItem.id
                        ).alias('part')
                    )
                    .where(
                        MetadataItem.metadata_type == MetadataItemType.Show,
                        (
                            (MetadataItemSettings.id >> None) |
                            (MetadataItemSettings.account == account)
                        )
                    )
        )

        # Prime `Matcher` cache
        if self.matcher.cache is not None and hasattr(self.matcher.cache, 'prime'):
            context = self.matcher.cache.prime(force=True)
        else:
            context = PrimeContext()

        def shows_iterator():
            x = 0

            for show in shows:
                # Parse `guid` (if enabled, and not already parsed)
                if parse_guid:
                    raw, parsed = show['guid']

                    if parsed is None:
                        show['guid'] = (raw, Guid.parse(raw))

                # Pick `guid` based on request (`parse_guid` parameter)
                guid_raw, guid_parsed = show['guid']
                guid = guid_parsed if parse_guid else guid_raw

                yield x, guid, show['settings']
                x += 1

        def episodes_iterator():
            for item in episodes.tuples().iterator():
                # Expand `item` tuple
                (
                    show_id, season_id,
                    episode_id, episode_index,
                    rating, view_offset, last_viewed_at,
                    duration, file
                ) = item

                # Retrieve parents
                show = shows.get(show_id)

                if show is None:
                    log.debug('Unable to find show by id: %r', show_id)
                    continue

                season = seasons.get(season_id)

                if season is None:
                    log.debug('Unable to find season by id: %r', season_id)
                    continue

                # Parse `guid` (if enabled, and not already parsed)
                if parse_guid:
                    raw, parsed = show['guid']

                    if parsed is None:
                        show['guid'] = (raw, Guid.parse(raw))

                # Build dictionary of settings
                settings = self.settings_video(rating, view_offset, last_viewed_at)

                # Pick `guid` based on request (`parse_guid` parameter)
                guid_raw, guid_parsed = show['guid']
                guid = guid_parsed if parse_guid else guid_raw

                # Use primed `Matcher` buffer
                with context:
                    # Run `Matcher` on episode
                    season_num, episode_nums = self.matcher.process_episode(
                        episode_id,
                        (season['index'], episode_index),
                        file
                    )

                for episode_num in episode_nums:
                    ids = {
                        'show': show_id,
                        'season': season_id,
                        'episode': episode_id
                    }

                    yield ids, guid, (season_num, episode_num), {
                        'duration': duration,
                        'settings': settings
                    }

        return shows_iterator(), seasons, episodes_iterator()


class Library(object):
    matcher = Matcher

    movies = MovieLibrary()
    shows = ShowLibrary()
    seasons = SeasonLibrary()
    episodes = EpisodeLibrary()

    def __init__(self, matcher):
        self.matcher = matcher

        self.movies = MovieLibrary(self)
        self.shows = ShowLibrary(self)
        self.seasons = SeasonLibrary(self)
        self.episodes = EpisodeLibrary(self)

    @classmethod
    def sections(cls, section_type, *fields, **kwargs):
        agent_required = kwargs.pop('agent_required', True)

        filter = []

        if type(section_type) is list:
            # `section_type` is a list
            filter.append(LibrarySection.section_type << section_type)
        else:
            # `section_type` is an integer
            filter.append(LibrarySection.section_type == section_type)

        if agent_required is True:
            # Filter out any sections without metadata agents
            filter.append(LibrarySection.agent != "com.plexapp.agents.none")

        if fields:
            # Return specific fields from table
            return LibrarySection.select(*fields).where(*filter)

        return LibrarySection.select().where(*filter)

    @classmethod
    def media(cls, sections, include_episodes=False):
        pass
