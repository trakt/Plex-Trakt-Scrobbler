from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.core.guid import GuidMatch, GuidParser
from plugin.sync.modes.core.base import log_unsupported, mark_unsupported
from plugin.sync.modes.pull.base import Base

from plex_database.models import MetadataItem
import elapsed
import logging

log = logging.getLogger(__name__)


class Shows(Base):
    data = [
        SyncData.Collection,
        SyncData.Playback,
        SyncData.Ratings,
        SyncData.Watched
    ]

    def __init__(self, task):
        super(Shows, self).__init__(task)

        # Sections
        self.p_sections = None
        self.p_sections_map = None

        # Shows
        self.p_shows = None
        self.p_shows_unsupported = None

        # Seasons
        self.p_seasons = None

        # Episodes
        self.p_episodes = None

        self.p_pending = None

    @elapsed.clock
    def construct(self):
        # Retrieve show sections
        self.p_sections, self.p_sections_map = self.sections('show')

    @elapsed.clock
    def start(self):
        # Fetch episodes with account settings
        self.p_shows, self.p_seasons, self.p_episodes = self.plex.library.episodes.mapped(
            self.p_sections, ([
                MetadataItem.library_section
            ], [], []),
            account=self.current.account.plex.key,
            parse_guid=True
        )

        # TODO process seasons

        # Calculate total number of episodes
        self.p_pending = {}

        for data in self.get_data(SyncMedia.Episodes):
            t_episodes = [
                (key, se, ep)
                for key, t_show in self.trakt[(SyncMedia.Episodes, data)].items()
                for se, t_season in t_show.seasons.items()
                for ep in t_season.episodes.iterkeys()
            ]

            if data not in self.p_pending:
                self.p_pending[data] = {}

            for key in t_episodes:
                self.p_pending[data][key] = False

        # Reset state
        self.p_shows_unsupported = {}

    #
    # Run
    #

    @elapsed.clock
    def run(self):
        self.run_shows()
        self.run_episodes()

        # Log details
        log_unsupported(log, 'Found %d unsupported show(s)', self.p_shows_unsupported)
        log.debug('Pending: %r', self.p_pending)

    def run_shows(self):
        for sh_id, guid, p_show in self.p_shows:
            # Parse guid
            match = GuidParser.parse(guid)

            if not match.supported:
                mark_unsupported(self.p_shows_unsupported, sh_id, guid)
                continue

            if not match.found:
                log.info('Unable to find identifier for: %s/%s (rating_key: %r)', guid.service, guid.id, sh_id)
                continue

            key = (match.guid.service, match.guid.id)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table('shows').get(key)

            # Store in item map
            self.current.map.add(p_show.get('library_section'), sh_id, [key, pk])

            if pk is None:
                # No `pk` found
                continue

            # Execute data handlers
            for data in self.get_data(SyncMedia.Shows):
                t_show = self.trakt[(SyncMedia.Shows, data)].get(pk)

                # Execute show handlers
                self.execute_handlers(
                    SyncMedia.Shows, data,
                    key=sh_id,

                    p_item=p_show,
                    t_item=t_show
                )

    def run_episodes(self):
        for ids, guid, (season_num, episode_num), p_show, p_season, p_episode in self.p_episodes:
            # Process `p_guid` (map + validate)
            match = GuidParser.parse(guid, (season_num, episode_num))

            if not match.supported:
                mark_unsupported(self.p_shows_unsupported, ids['show'], guid)
                continue

            if not match.found:
                log.info('Unable to find identifier for: %s/%s (rating_key: %r)', guid.service, guid.id, ids['show'])
                continue

            # Process episode
            self.run_episode(ids, match, p_show, p_episode)

            # Task checkpoint
            self.checkpoint()

    def run_episode(self, ids, match, p_show, p_episode):
        key = (match.guid.service, match.guid.id)

        # Determine media type
        if match.media == GuidMatch.Media.Movie:
            c_media = 'movies'
            s_media = SyncMedia.Movies
        elif match.media == GuidMatch.Media.Episode:
            c_media = 'shows'
            s_media = SyncMedia.Episodes
        else:
            raise ValueError('Unknown match media type: %r' % (match.media,))

        # Try retrieve `pk` for `key`
        pk = self.trakt.table(c_media).get(key)

        if pk is None:
            return

        if not ids.get('episode'):
            return

        # Process actions for episode
        for data in self.get_data(s_media):
            # Find item
            t_item = self.trakt[(s_media, data)].get(pk)

            if t_item is None:
                continue

            # Run episode action
            self.run_episode_action(
                ids, match,
                p_show, p_episode,
                data, t_item
            )

    def run_episode_action(self, ids, match, p_show, p_episode, data, t_item):
        if match.media == GuidMatch.Media.Movie:
            # Process movie
            self.execute_episode_action(
                ids, match,
                p_show, p_episode,
                data, t_item
            )
        elif match.media == GuidMatch.Media.Episode:
            # Ensure `match` contains episodes
            if not match.episodes:
                log.info('No episodes returned for: %s/%s', match.guid.service, match.guid.id)
                return

            # Process each episode
            for season_num, episode_num in match.episodes:
                t_season = t_item.seasons.get(season_num)

                if t_season is None:
                    # Unable to find matching season in `t_show`
                    continue

                t_episode = t_season.episodes.get(episode_num)

                if t_episode is None:
                    # Unable to find matching episode in `t_season`
                    continue

                self.execute_episode_action(
                    ids, match,
                    p_show, p_episode,
                    data, t_episode
                )

    def execute_episode_action(self, ids, match, p_show, p_episode, data, t_item):
        # Process episode
        if match.media == GuidMatch.Media.Episode:
            # Process episode
            self.execute_handlers(
                SyncMedia.Episodes, data,
                key=ids['episode'],

                p_item=p_episode,
                t_item=t_item
            )

            return True

        # Process movie
        if match.media == GuidMatch.Media.Movie:
            # Build movie item from plex episode
            p_movie = p_episode.copy()

            p_movie['title'] = p_show.get('title')
            p_movie['year'] = p_show.get('year')

            # Process movie
            self.execute_handlers(
                SyncMedia.Movies, data,
                key=ids['episode'],

                p_item=p_episode,
                t_item=t_item
            )
            return True

        raise ValueError('Unknown media type: %r' % (match.media,))
