from plugin.sync.core.enums import SyncMedia, SyncData
from plugin.sync.core.guid import GuidMatch, GuidParser
from plugin.sync.modes.core.base import log_unsupported, mark_unsupported
from plugin.sync.modes.push.base import Base

from plex_database.models import MetadataItem, MediaItem, Episode
from plex_metadata import Guid
import copy
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
        self.p_shows_count = None
        self.p_shows_unsupported = None

        # Seasons
        self.p_seasons = None

        # Episodes
        self.p_episodes = None
        self.p_episodes_count = None

    @elapsed.clock
    def construct(self):
        # Retrieve movie sections
        self.p_sections, self.p_sections_map = self.sections('show')

        # Determine number of shows that will be processed
        self.p_shows_count = self.plex.library.shows.count(
            self.p_sections
        )

        # Determine number of shows that will be processed
        self.p_episodes_count = self.plex.library.episodes.count_items(
            self.p_sections
        )

        # Increment progress steps total
        self.current.progress.group(Shows, 'matched:shows').add(self.p_shows_count)
        self.current.progress.group(Shows, 'matched:episodes').add(self.p_episodes_count)
        self.current.progress.group(Shows, 'missing:shows')
        self.current.progress.group(Shows, 'missing:episodes')

    @elapsed.clock
    def start(self):
        super(Shows, self).start()

        # Fetch movies with account settings
        self.p_shows, self.p_seasons, self.p_episodes = self.plex.library.episodes.mapped(
            self.p_sections, ([
                MetadataItem.title,
                MetadataItem.year
            ], [], [
                MediaItem.audio_channels,
                MediaItem.audio_codec,
                MediaItem.height,
                MediaItem.interlaced,

                Episode.added_at
            ]),
            account=self.current.account.plex.key,
            parse_guid=True
        )

        # Update pending item collections
        self.current.pending.create('shows', self.trakt.table.show_keys.copy())
        self.current.pending.create('episodes', copy.deepcopy(self.trakt.table.episode_keys))

        # Reset state
        self.p_shows_unsupported = {}

    #
    # Run
    #

    @elapsed.clock
    def run(self):
        self.run_shows()
        self.run_episodes()

    @elapsed.clock
    def run_shows(self):
        # Iterate over plex shows
        for sh_id, guid, p_show in self.p_shows:
            # Increment one step
            self.current.progress.group(Shows, 'matched:shows').step()

            # Process `p_guid` (map + validate)
            match = GuidParser.parse(guid)

            if not match.supported:
                mark_unsupported(self.p_shows_unsupported, sh_id, guid)
                continue

            if not match.found:
                log.info('Unable to find identifier for: %s/%s (rating_key: %r)', guid.service, guid.id, sh_id)
                continue

            # Process show
            self.run_show(sh_id, match, p_show)

            # Task checkpoint
            self.checkpoint()

        # Stop progress group
        self.current.progress.group(Shows, 'matched:shows').stop()

    def run_show(self, sh_id, match, p_show):
        # Try retrieve `pk` for `key`
        pk = self.trakt.table('shows').get((match.guid.service, match.guid.id))

        # Process show (execute handlers)
        self.execute_show(
            sh_id, pk, match.guid,
            p_show
        )

        # Remove show from pending items collection
        self.current.pending['shows'].remove(pk)

    @elapsed.clock
    def run_episodes(self):
        # Iterate over plex episodes
        for ids, guid, (season_num, episode_num), p_show, p_season, p_episode in self.p_episodes:
            # Increment one step
            self.current.progress.group(Shows, 'matched:episodes').step()

            # Parse guid
            match = GuidParser.parse(guid, (season_num, episode_num))

            if not match.supported:
                mark_unsupported(self.p_shows_unsupported, ids['show'], guid)
                continue

            if not match.found:
                log.info('Unable to find identifier for: %s/%s (rating_key: %r)', guid.service, guid.id, ids['show'])
                continue

            # Process episode
            self.run_episode(
                ids, match,
                p_show, p_season, p_episode
            )

            # Task checkpoint
            self.checkpoint()

        # Stop progress group
        self.current.progress.group(Shows, 'matched:episodes').stop()

    def run_episode(self, ids, match, p_show, p_season, p_episode):
        # Try retrieve `pk` for `key`
        pk = self.trakt.table(match.table_key).get((
            match.guid.service,
            match.guid.id
        ))

        # Process episode
        if match.media == GuidMatch.Media.Episode:
            # Ensure `match` contains episodes
            if not match.episodes:
                log.info('No episodes returned for: %s/%s', match.guid.service, match.guid.id)
                return

            # Process each episode
            for identifier in match.episodes:
                # Execute handlers for episode
                self.execute_episode(
                    ids['episode'], pk, match.guid, identifier,
                    p_show, p_season, p_episode
                )

                # Remove episode from pending items collection
                self.current.pending['episodes'].remove(pk, identifier)

            return True

        # Process movie
        if match.media == GuidMatch.Media.Movie:
            # Build movie item from plex episode
            p_movie = p_episode.copy()

            p_movie['title'] = p_show.get('title')
            p_movie['year'] = p_show.get('year')

            # Execute handlers for movie
            self.execute_movie(
                ids['episode'], pk, match.guid,
                p_movie
            )

            # Remove episode from pending items collection
            self.current.pending['movies'].remove(pk)
            return True

        raise ValueError('Unknown media type: %r' % (match.media,))

    #
    # Finish
    #

    @elapsed.clock
    def finish(self):
        log_unsupported(log, 'Found %d unsupported show(s)', self.p_shows_unsupported)

        # Process missing items
        self.finish_shows()
        self.finish_episodes()

    @elapsed.clock
    def finish_shows(self):
        if self.current.kwargs.get('section'):
            # Collection cleaning disabled for individual syncs
            return

        # Increment progress steps
        self.current.progress.group(Shows, 'missing:shows').add(len(self.current.pending['shows'].keys))

        # Iterate over trakt shows (that aren't in plex)
        for pk in list(self.current.pending['shows'].keys):
            # Increment one step
            self.current.progress.group(Shows, 'missing:shows').step()

            # Iterate over data handlers
            triggered = False

            for data in self.get_data(SyncMedia.Shows):
                if data not in [SyncData.Collection]:
                    continue

                # Retrieve show
                t_show = self.trakt[(SyncMedia.Shows, data)].get(pk)

                if not t_show:
                    continue

                log.debug('Found show missing from plex: %r [data: %r]', pk, SyncData.title(data))

                # Trigger handler
                self.execute_handlers(
                    self.mode, SyncMedia.Shows, data,

                    key=None,

                    guid=Guid.construct(*pk, matched=True),
                    p_item=None,

                    t_item=t_show
                )

                # Mark triggered
                triggered = True

            # Check if action was triggered
            if not triggered:
                continue

            # Remove movie from `pending` set
            self.current.pending['shows'].keys.remove(pk)

        # Stop progress group
        self.current.progress.group(Shows, 'missing:shows').stop()

        self.log_pending(
            log, 'Unable to find %d show(s) in Plex, list has been saved to: %s',
            self.current.account, 'shows', self.current.pending['shows'].keys
        )

    @elapsed.clock
    def finish_episodes(self):
        if self.current.kwargs.get('section'):
            # Collection cleaning disabled for individual syncs
            return

        # Increment progress steps
        self.current.progress.group(Shows, 'missing:episodes').add(len(self.current.pending['episodes'].keys))

        # Iterate over trakt episodes (that aren't in plex)
        for pk, episodes in [(p, list(e)) for (p, e) in self.current.pending['episodes'].keys.items()]:
            # Increment one step
            self.current.progress.group(Shows, 'missing:episodes').step()

            # Iterate over trakt episodes (that aren't in plex)
            for identifier in episodes:
                # Iterate over data handlers
                season_num, episode_num = identifier
                triggered = False

                for data in self.get_data(SyncMedia.Episodes):
                    if data not in [SyncData.Collection]:
                        continue

                    # Retrieve episode
                    t_show, t_season, t_episode = self.t_objects(
                        self.trakt[(SyncMedia.Episodes, data)], pk,
                        season_num, episode_num
                    )

                    if not t_episode:
                        continue

                    log.debug('Found episode missing from plex: %r - %r [data: %r]', pk, identifier, SyncData.title(data))

                    # Trigger handler
                    self.execute_handlers(
                        self.mode, SyncMedia.Episodes, data,
                        key=None,
                        identifier=identifier,
                        guid=Guid.construct(*pk, matched=True),

                        p_show=None,
                        p_item=None,

                        t_show=t_show,
                        t_item=t_episode
                    )

                    # Mark triggered
                    triggered = True

                # Check if action was triggered
                if not triggered:
                    continue

                # Remove movie from `pending` set
                self.current.pending['episodes'].keys[pk].remove(identifier)

        # Stop progress group
        self.current.progress.group(Shows, 'missing:episodes').stop()

        self.log_pending(
            log, 'Unable to find %d episode(s) in Plex, list has been saved to: %s',
            self.current.account, 'episodes', self.current.pending['episodes'].keys
        )
