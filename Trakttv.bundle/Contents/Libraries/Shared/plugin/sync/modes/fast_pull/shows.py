from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.modes.core.base import Mode, log_unsupported, mark_unsupported

from plex_database.models import MetadataItem
from trakt_sync.cache.main import Cache
import elapsed
import logging

log = logging.getLogger(__name__)


class Shows(Mode):
    data = [
        SyncData.Collection,
        SyncData.Playback,
        SyncData.Ratings,
        SyncData.Watched
    ]
    mode = SyncMode.FastPull

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
        # Retrieve show sections
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
        self.current.progress.group(Shows, 'shows').add(self.p_shows_count)
        self.current.progress.group(Shows, 'episodes').add(self.p_episodes_count)

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

        # Reset state
        self.p_shows_unsupported = {}

    @elapsed.clock
    def run(self):
        # TODO process seasons

        with elapsed.clock(Shows, 'run:shows'):
            # Process shows
            for sh_id, p_guid, p_show in self.p_shows:
                # Increment one step
                self.current.progress.group(Shows, 'shows').step()

                # Process `p_guid` (map + validate)
                supported, p_guid = self.process_guid(p_guid)

                if not supported:
                    mark_unsupported(self.p_shows_unsupported, sh_id, p_guid)
                    continue

                key = (p_guid.service, p_guid.id)

                # Try retrieve `pk` for `key`
                pk = self.trakt.table('shows').get(key)

                # Store in item map
                self.current.map.add(p_show.get('library_section'), sh_id, [key, pk])

                if pk is None:
                    # No `pk` found
                    continue

                # Iterate over changed data
                for key, result in self.trakt.changes:
                    media, data = key[0:2]

                    if media != SyncMedia.Shows:
                        # Ignore changes that aren't for episodes
                        continue

                    if data == SyncData.Watchlist:
                        # Ignore watchlist data
                        continue

                    if not self.is_data_enabled(data):
                        # Data type has been disabled
                        continue

                    data_name = Cache.Data.get(data)

                    if data_name not in result.changes:
                        # No changes for collection
                        continue

                    for action, shows in result.changes[data_name].items():
                        t_show = shows.get(pk)

                        if t_show is None:
                            # Unable to find matching show in trakt data
                            continue

                        # Execute show handlers
                        self.execute_handlers(
                            SyncMedia.Shows, data,
                            action=action,

                            key=sh_id,

                            p_item=p_show,
                            t_item=t_show
                        )

        # Stop progress group
        self.current.progress.group(Shows, 'shows').stop()

        with elapsed.clock(Shows, 'run:episodes'):
            # Process episodes
            for ids, p_guid, (season_num, episode_num), p_show, p_season, p_episode in self.p_episodes:
                # Increment one step
                self.current.progress.group(Shows, 'episodes').step()

                # Process `p_guid` (map + validate)
                supported, p_guid, season_num, episode_num = self.process_guid_episode(p_guid, season_num, episode_num)

                if not supported:
                    mark_unsupported(self.p_shows_unsupported, ids['show'], p_guid)
                    continue

                key = (p_guid.service, p_guid.id)

                # Try retrieve `pk` for `key`
                pk = self.trakt.table('shows').get(key)

                if pk is None:
                    # No `pk` found
                    continue

                if not ids.get('episode'):
                    # Missing `episode` rating key
                    continue

                for key, result in self.trakt.changes:
                    media, data = key[0:2]

                    if media != SyncMedia.Episodes:
                        # Ignore changes that aren't for episodes
                        continue

                    if not self.is_data_enabled(data):
                        # Data type has been disabled
                        continue

                    data_name = Cache.Data.get(data)

                    if data_name not in result.changes:
                        # No changes for collection
                        continue

                    for action, shows in result.changes[data_name].items():
                        t_show = shows.get(pk)

                        if t_show is None:
                            # Unable to find matching show in trakt data
                            continue

                        t_season = t_show.get('seasons', {}).get(season_num)

                        if t_season is None:
                            # Unable to find matching season in `t_show`
                            continue

                        t_episode = t_season.get('episodes', {}).get(episode_num)

                        if t_episode is None:
                            # Unable to find matching episode in `t_season`
                            continue

                        self.execute_handlers(
                            SyncMedia.Episodes, data,
                            action=action,
                            key=ids['episode'],

                            p_item=p_episode,
                            t_item=t_episode
                        )

                # Task checkpoint
                self.checkpoint()

        # Stop progress group
        self.current.progress.group(Shows, 'episodes').stop()

        # Log details
        log_unsupported(log, 'Found %d unsupported show(s)', self.p_shows_unsupported)
