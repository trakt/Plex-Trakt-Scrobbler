from plugin.sync.core.enums import SyncMedia
from plugin.sync.modes.core.base.mode import Mode

from plex import Plex
import logging
import trakt.objects

log = logging.getLogger(__name__)


class PullListsMode(Mode):
    @staticmethod
    def get_media(t_item):
        if type(t_item) is trakt.objects.Movie:
            return SyncMedia.Movies

        if type(t_item) is trakt.objects.Show:
            return SyncMedia.Shows

        # TODO implement season/episode items

        # if type(t_item) is trakt.objects.Season:
        #     return SyncMedia.Seasons
        #
        # if type(t_item) is trakt.objects.Episode:
        #     return SyncMedia.Episodes

        return None

    @staticmethod
    def get_playlists():
        container = Plex['playlists'].all(playlist_type='video')

        if not container:
            return

        for playlist in container:
            yield playlist.title.lower(), playlist

    def get_playlist(self, p_playlists, uri, title):
        if p_playlists is None or not uri or not title:
            log.warn('Unable to create/retrieve playlist for: %r', title)
            return None

        # Try find existing playlist
        p_playlist = p_playlists.get(title.lower())

        if p_playlist:
            return p_playlist

        # Create new playlist
        return self.create_playlist(uri, title)

    def create_playlist(self, uri, title):
        log.debug('Creating new playlist %r for account %r', title, self.current.account.id)

        p_playlist = Plex['playlists'].create(
            type='video',
            title=title,
            uri=uri
        ).first()

        if p_playlist is None:
            log.warn('Unable to create/retrieve playlist for: %r', title)
            return None

        return p_playlist
