from plugin.sync.core.constants import GUID_AGENTS
from plugin.sync.core.enums import SyncMedia
from plugin.sync.modes.core.base import log_unsupported, mark_unsupported
from plugin.sync.modes.pull.base import Base

from plex_database.models import MetadataItem
import elapsed
import logging

log = logging.getLogger(__name__)


class Shows(Base):
    @elapsed.clock
    def run(self):
        # Retrieve show sections
        p_sections, p_sections_map = self.sections('show')

        # Fetch episodes with account settings
        p_shows, p_seasons, p_episodes = self.plex.library.episodes.mapped(
            p_sections, ([
                MetadataItem.library_section
            ], [], []),
            account=self.current.account.plex.key,
            parse_guid=True
        )

        # TODO process seasons

        # Calculate total number of episodes
        pending = {}

        for data in self.get_data(SyncMedia.Episodes):
            t_episodes = [
                (key, se, ep)
                for key, t_show in self.trakt[(SyncMedia.Episodes, data)].items()
                for se, t_season in t_show.seasons.items()
                for ep in t_season.episodes.iterkeys()
            ]

            if data not in pending:
                pending[data] = {}

            for key in t_episodes:
                pending[data][key] = False

        # Task started
        unsupported_shows = {}

        # Process shows
        for sh_id, guid, p_show in p_shows:
            if not guid or guid.agent not in GUID_AGENTS:
                mark_unsupported(unsupported_shows, sh_id, guid, p_show)
                continue

            key = (guid.agent, guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

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

        # Process episodes
        for ids, guid, (season_num, episode_num), p_show, p_season, p_episode in p_episodes:
            if not guid or guid.agent not in GUID_AGENTS:
                mark_unsupported(unsupported_shows, ids['show'], guid, p_show)
                continue

            key = (guid.agent, guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            if pk is None:
                # No `pk` found
                continue

            if not ids.get('episode'):
                # Missing `episode` rating key
                continue

            for data in self.get_data(SyncMedia.Episodes):
                t_show = self.trakt[(SyncMedia.Episodes, data)].get(pk)

                if t_show is None:
                    # Unable to find matching show in trakt data
                    continue

                t_season = t_show.seasons.get(season_num)

                if t_season is None:
                    # Unable to find matching season in `t_show`
                    continue

                t_episode = t_season.episodes.get(episode_num)

                if t_episode is None:
                    # Unable to find matching episode in `t_season`
                    continue

                self.execute_handlers(
                    SyncMedia.Episodes, data,
                    key=ids['episode'],

                    p_item=p_episode,
                    t_item=t_episode
                )

                # Increment one step
                self.step(pending, data, (pk, season_num, episode_num))

            # Task checkpoint
            self.checkpoint()

        # Log details
        log_unsupported(log, 'Found %d unsupported show(s)\n%s', unsupported_shows)
        log.debug('Pending: %r', pending)
