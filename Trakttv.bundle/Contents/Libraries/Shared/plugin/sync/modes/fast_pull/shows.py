from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.core.guid import GuidMatch, GuidParser
from plugin.sync.modes.core.base import log_unsupported, mark_unsupported
from plugin.sync.modes.fast_pull.base import Base

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
                MetadataItem.library_section,
                MetadataItem.added_at
            ], [], [
                MetadataItem.added_at
            ]),
            account=self.current.account.plex.key,
            parse_guid=True
        )

        # Reset state
        self.p_shows_unsupported = {}

    #
    # Run
    #

    @elapsed.clock
    def run(self):
        # TODO process seasons
        self.run_shows()
        self.run_episodes()

        # Log details
        log_unsupported(log, 'Found %d unsupported show(s)', self.p_shows_unsupported)

    def run_shows(self):
        # Iterate over plex shows
        for sh_id, guid, p_show in self.p_shows:
            # Increment one step
            self.current.progress.group(Shows, 'shows').step()

            # Parse guid
            match = GuidParser.parse(guid)

            if not match.supported:
                mark_unsupported(self.p_shows_unsupported, sh_id, guid)
                continue

            if not match.found:
                log.info('Unable to find identifier for: %s/%s (rating_key: %r)', guid.service, guid.id, sh_id)
                continue

            # Process show
            self.run_show(sh_id, match, p_show)

        # Stop progress group
        self.current.progress.group(Shows, 'shows').stop()

    def run_show(self, sh_id, match, p_show):
        key = (match.guid.service, match.guid.id)

        # Try retrieve `pk` for `key`
        pk = self.trakt.table('shows').get(key)

        # Store in item map
        self.current.map.add(p_show.get('library_section'), sh_id, [key, pk])

        if pk is None:
            # No `pk` found
            return

        # Run pull handlers if the item has been added recently
        if self.should_pull(sh_id, p_show.get('added_at')):
            log.info('Show %r has been added recently, running pull sync instead', sh_id)

            # Execute handlers
            for data in self.get_data(SyncMedia.Shows):
                t_show = self.trakt[(SyncMedia.Shows, data)].get(pk)

                # Execute show handlers
                self.execute_handlers(
                    SyncMode.Pull, SyncMedia.Shows, data,
                    key=sh_id,

                    p_item=p_show,
                    t_item=t_show
                )
        else:
            # Execute handlers for changed data
            for data, action, t_show in self.iter_changes(SyncMedia.Shows, pk):
                # Execute show handlers
                self.execute_handlers(
                    self.mode, SyncMedia.Shows, data,
                    action=action,

                    key=sh_id,

                    p_item=p_show,
                    t_item=t_show
                )

    def run_episodes(self):
        # Iterate over plex episodes
        for ids, guid, (season_num, episode_num), p_show, p_season, p_episode in self.p_episodes:
            # Increment one step
            self.current.progress.group(Shows, 'episodes').step()

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

        # Stop progress group
        self.current.progress.group(Shows, 'episodes').stop()

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

        # Run pull handlers if the item has been added recently
        if self.should_pull(ids['episode'], p_episode.get('added_at')):
            log.info('Episode %r has been added recently, running pull sync instead', ids['episode'])

            # Execute handlers
            for data in self.get_data(s_media):
                t_item = self.trakt[(s_media, data)].get(pk)

                if t_item is None:
                    continue

                self.run_episode_action(
                    SyncMode.Pull, data, ids, match,
                    p_show, p_episode, t_item
                )
        else:
            # Execute handlers for changed data
            for data, action, t_item in self.iter_changes(s_media, pk):
                self.run_episode_action(
                    self.mode, data, ids, match,
                    p_show, p_episode, t_item,
                    action=action
                )
