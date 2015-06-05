from plugin.sync.core.enums import SyncMode, SyncMedia
from plugin.sync.modes.core.base import Mode, TRAKT_DATA_MAP

from plex_database.models import LibrarySectionType, LibrarySection
import logging

log = logging.getLogger(__name__)


class Base(Mode):
    mode = SyncMode.Pull


class Movies(Base):
    def run(self):
        # Retrieve movie sections
        p_sections = self.plex.library.sections(
            LibrarySectionType.Movie,
            LibrarySection.id
        ).tuples()

        # Fetch movies with account settings
        p_items = self.plex.library.movies.mapped(
            p_sections,
            account=self.current.account.plex.id,
            parse_guid=True
        )

        # Task started
        for rating_key, p_guid, p_item in p_items:
            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            for data in TRAKT_DATA_MAP[SyncMedia.Movies]:
                t_movie = self.trakt[(SyncMedia.Movies, data)].get(pk)

                self.execute_handlers(
                    SyncMedia.Movies, data,
                    rating_key=rating_key,

                    p_item=p_item,
                    t_item=t_movie
                )


class Shows(Base):
    pass


class Push(Mode):
    mode = SyncMode.Push

    children = [
        Movies,
        Shows
    ]

    def run(self):
        # Fetch changes from trakt.tv
        self.trakt.refresh()

        # Build key table for lookups
        self.trakt.build_table()

        # Run children
        self.execute_children()
