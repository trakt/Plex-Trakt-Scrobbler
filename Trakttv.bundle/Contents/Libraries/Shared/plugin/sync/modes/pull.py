from plugin.sync.core.enums import SyncMode, SyncMedia
from plugin.sync.modes.core.base import Mode, TRAKT_DATA_MAP

from plex_database.models import LibrarySectionType, LibrarySection
import logging

log = logging.getLogger(__name__)


class Movies(Mode):
    mode = SyncMode.Pull

    def run(self):
        # Retrieve movie sections
        p_sections = self.plex.library.sections(
            LibrarySectionType.Movie,
            LibrarySection.id
        ).tuples()

        # Fetch movies with account settings
        # TODO use actual `account`
        p_items = self.plex.library.movies.mapped(
            p_sections,
            account=1,
            parse_guid=True
        )

        for rating_key, p_guid, p_settings in p_items:
            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            if pk is None:
                # No `pk` found
                continue

            for data in TRAKT_DATA_MAP[SyncMedia.Movies]:
                t_items = self.trakt[(SyncMedia.Movies, data)]
                t_item = t_items.get(pk)

                self.execute_handlers(
                    SyncMedia.Movies, data,
                    rating_key=rating_key,
                    p_settings=p_settings,
                    t_item=t_item
                )


class Pull(Mode):
    mode = SyncMode.Pull

    children = [
        Movies
    ]

    def run(self):
        # Fetch changes from trakt.tv
        self.trakt.refresh()

        # Build key table for lookups
        self.trakt.build_table()

        # Run children
        self.execute_children()

        # Flush caches to archives
        # self.current.state.flush()
