from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.handlers.core.base import DataHandler, MediaHandler

from plex_database.models import LibrarySectionType, LibrarySection
import logging

log = logging.getLogger(__name__)


class Movies(MediaHandler):
    media = SyncMedia.Movies

    def fast_pull(self, changes):
        # Retrieve movie sections
        p_sections = self.current.state.plex.library.sections(LibrarySectionType.Movie, LibrarySection.id).tuples()

        # Fetch movies with account settings
        p_items = self.current.state.plex.library.movies.mapped(p_sections, account=1, parse_guid=True)

        for _, p_guid, p_settings in p_items:
            key = (p_guid.agent, p_guid.sid)

            self.execute_actions(changes, key, p_settings)

    def on_added(self, key, p_settings, t_properties):
        log.debug('[%s] added - p_settings: %r, t_properties: %r', key, p_settings, t_properties)

        if p_settings.get('last_viewed_at'):
            # Already marked at watched in plex
            return

        # TODO mark item in plex as watched
        raise NotImplementedError

    @staticmethod
    def find_actions(changes, key):
        for action, items in changes.items():
            if key not in items:
                continue

            yield action, items[key]


class Watched(DataHandler):
    data = SyncData.Watched

    children = [
        Movies
    ]
