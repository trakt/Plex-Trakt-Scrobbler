from plugin.sync.core.constants import GUID_AGENTS
from plugin.sync.core.enums import SyncMode, SyncMedia
from plugin.sync.modes.core.base import Mode, log_unsupported, mark_unsupported

from plex_database.models import MetadataItem
from trakt_sync.cache.main import Cache
import elapsed
import logging

log = logging.getLogger(__name__)


class Shows(Mode):
    mode = SyncMode.FastPull

    @elapsed.clock
    def run(self):
        # Retrieve show sections
        p_sections, p_sections_map = self.sections('show')

        with elapsed.clock(Shows, 'run:fetch'):
            # Fetch episodes with account settings
            p_shows, p_seasons, p_episodes = self.plex.library.episodes.mapped(
                p_sections, ([
                    MetadataItem.library_section
                ], [], []),
                account=self.current.account.plex.key,
                parse_guid=True
            )

        # TODO process seasons

        # Calculate total number of episode changes
        total = 0

        for (media, data), result in self.trakt.changes:
            if media != SyncMedia.Episodes:
                # Ignore changes that aren't for episodes
                continue

            data_name = Cache.Data.get(data)

            for count in result.metrics.episodes.get(data_name, {}).itervalues():
                total += count

        # Task started
        unsupported_shows = {}

        self.current.progress.start(total)

        with elapsed.clock(Shows, 'run:shows'):
            # Process shows
            for sh_id, p_guid, p_show in p_shows:
                if not p_guid or p_guid.agent not in GUID_AGENTS:
                    mark_unsupported(unsupported_shows, sh_id, p_guid, p_show)
                    continue

                key = (p_guid.agent, p_guid.sid)

                # Try retrieve `pk` for `key`
                pk = self.trakt.table.get(key)

                if pk is None:
                    # No `pk` found
                    continue

                # Store in item map
                self.current.map.add(p_show.get('library_section'), sh_id, p_guid)

                for (media, data), result in self.trakt.changes:
                    if media != SyncMedia.Shows:
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

                        # Execute show handlers
                        self.execute_handlers(
                            SyncMedia.Shows, data,
                            action=action,

                            key=sh_id,

                            p_item=p_show,
                            t_item=t_show
                        )

        with elapsed.clock(Shows, 'run:episodes'):
            # Process episodes
            for ids, p_guid, (season_num, episode_num), p_show, p_season, p_episode in p_episodes:
                if not p_guid or p_guid.agent not in GUID_AGENTS:
                    mark_unsupported(unsupported_shows, ids['show'], p_guid, p_show)
                    continue

                key = (p_guid.agent, p_guid.sid)

                # Try retrieve `pk` for `key`
                pk = self.trakt.table.get(key)

                if pk is None:
                    # No `pk` found
                    continue

                if not ids.get('episode'):
                    # Missing `episode` rating key
                    continue

                for (media, data), result in self.trakt.changes:
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

                        # Increment one step
                        self.current.progress.step()

                # Task checkpoint
                self.checkpoint()

        # Log details
        log_unsupported(log, 'Found %d unsupported show(s)\n%s', unsupported_shows)

        # Task stopped
        self.current.progress.stop()
