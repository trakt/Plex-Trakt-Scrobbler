from plugin.core.constants import GUID_SERVICES
from plugin.sync.core.enums import SyncMedia, SyncData
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
        self.p_shows_pending = None
        self.p_shows_unsupported = None

        # Seasons
        self.p_seasons = None

        # Episodes
        self.p_episodes = None
        self.p_episodes_count = None
        self.p_episodes_pending = None

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

        # Reset state
        self.p_shows_pending = self.trakt.table.shows.copy()
        self.p_shows_unsupported = {}

        self.p_episodes_pending = copy.deepcopy(self.trakt.table.episodes)

    @elapsed.clock
    def run(self):
        # Process matched items
        self.process_matched_shows()
        self.process_matched_episodes()

        # Report unsupported shows
        log_unsupported(log, 'Found %d unsupported show(s)\n%s', self.p_shows_unsupported)

        # Process missing items
        self.process_missing_shows()
        self.process_missing_episodes()

    #
    # Shows
    #

    @elapsed.clock
    def process_matched_shows(self):
        # Iterate over plex shows
        for sh_id, guid, p_show in self.p_shows:
            # Increment one step
            self.current.progress.group(Shows, 'matched:shows').step()

            # Ensure `guid` is available
            if not guid or guid.agent not in GUID_SERVICES:
                mark_unsupported(self.p_shows_unsupported, sh_id, guid, p_show)
                continue

            key = (guid.agent, guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            for data in self.get_data(SyncMedia.Shows):
                t_show = self.trakt[(SyncMedia.Shows, data)].get(pk)

                # Execute show handlers
                self.execute_handlers(
                    SyncMedia.Shows, data,
                    key=sh_id,
                    guid=guid,

                    p_item=p_show,

                    t_item=t_show
                )

            # Remove show from `pending_shows`
            if pk and pk in self.p_shows_pending:
                self.p_shows_pending.remove(pk)

            # Task checkpoint
            self.checkpoint()

        # Stop progress group
        self.current.progress.group(Shows, 'matched:shows').stop()

    @elapsed.clock
    def process_missing_shows(self):
        if self.current.kwargs.get('section'):
            # Collection cleaning disabled for individual syncs
            return

        # Increment progress steps
        self.current.progress.group(Shows, 'missing:shows').add(len(self.p_shows_pending))

        # Iterate over trakt shows (that aren't in plex)
        for pk in list(self.p_shows_pending):
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
                    SyncMedia.Shows, data,

                    key=None,

                    guid=Guid(*pk),
                    p_item=None,

                    t_item=t_show
                )

                # Mark triggered
                triggered = True

            # Check if action was triggered
            if not triggered:
                continue

            # Remove movie from `pending` set
            self.p_shows_pending.remove(pk)

        # Stop progress group
        self.current.progress.group(Shows, 'missing:shows').stop()

        self.log_pending('Unable to find %d show(s) in Plex\n%s', self.p_shows_pending)

    #
    # Episodes
    #

    @elapsed.clock
    def process_matched_episodes(self):
        # Iterate over plex episodes
        for ids, guid, (season_num, episode_num), p_show, p_season, p_episode in self.p_episodes:
            # Increment one step
            self.current.progress.group(Shows, 'matched:episodes').step()

            # Ensure `guid` is available
            if not guid or guid.agent not in GUID_SERVICES:
                mark_unsupported(self.p_shows_unsupported, ids['show'], guid, p_show)
                continue

            key = (guid.agent, guid.sid)
            identifier = (season_num, episode_num)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            with elapsed.clock(Shows, 'run:plex_episodes:execute_handlers'):
                for data in self.get_data(SyncMedia.Episodes):
                    with elapsed.clock(Shows, 'run:plex_episodes:t_objects'):
                        t_show, t_season, t_episode = self.t_objects(
                            self.trakt[(SyncMedia.Episodes, data)], pk,
                            season_num, episode_num
                        )

                    # Execute episode handlers
                    self.execute_handlers(
                        SyncMedia.Episodes, data,

                        key=ids['episode'],
                        identifier=identifier,

                        guid=guid,
                        p_show=p_show,
                        p_item=p_episode,

                        t_show=t_show,
                        t_item=t_episode
                    )

            # Remove episode from `pending_episodes`
            if pk in self.p_episodes_pending and identifier in self.p_episodes_pending[pk]:
                self.p_episodes_pending[pk].remove(identifier)

            # Task checkpoint
            self.checkpoint()

        # Stop progress group
        self.current.progress.group(Shows, 'matched:episodes').stop()

    @elapsed.clock
    def process_missing_episodes(self):
        if self.current.kwargs.get('section'):
            # Collection cleaning disabled for individual syncs
            return

        # Increment progress steps
        self.current.progress.group(Shows, 'missing:episodes').add(len(self.p_episodes_pending))

        # Iterate over trakt episodes (that aren't in plex)
        for pk, episodes in [(p, list(e)) for (p, e) in self.p_episodes_pending.items()]:
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
                        SyncMedia.Episodes, data,
                        key=None,
                        identifier=identifier,
                        guid=Guid(*pk),

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
                self.p_episodes_pending[pk].remove(identifier)

        # Stop progress group
        self.current.progress.group(Shows, 'missing:episodes').stop()

        self.log_pending('Unable to find %d episode(s) in Plex\n%s', self.p_episodes_pending)

    @staticmethod
    def t_objects(collection, pk, season_num, episode_num):
        # Try find trakt `Show` from `collection`
        t_show = collection.get(pk)

        if t_show is None:
            return t_show, None, None

        # Try find trakt `Season`
        t_season = t_show.seasons.get(season_num)

        if t_season is None:
            return t_show, t_season, None

        # Try find trakt `Episode`
        t_episode = t_season.episodes.get(episode_num)

        return t_show, t_season, t_episode
