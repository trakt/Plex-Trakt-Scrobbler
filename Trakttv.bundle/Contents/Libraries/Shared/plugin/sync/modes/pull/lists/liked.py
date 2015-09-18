from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.modes.core.base import Mode

from plex import Plex
from trakt import Trakt
import elapsed
import logging
import trakt.objects
import urllib

log = logging.getLogger(__name__)


class LikedLists(Mode):
    mode = SyncMode.Pull

    @elapsed.clock
    def run(self):
        log.debug('_by_guid: %r', self.current.map._by_guid)

        # Retrieve plex sections
        p_sections, p_sections_map = self.sections()

        # Retrieve plex playlists
        p_playlists = dict(self.get_playlists())

        # Process trakt lists
        for t_list in Trakt['users'].likes('lists'):
            self.process(p_playlists, p_sections_map, t_list)

    def process(self, p_playlists, p_sections_map, t_list):
        # Create/retrieve plex list
        playlist = self.get_playlist(p_playlists, t_list)

        playlist_items = dict([
            (int(item.rating_key), item)
            for item in playlist.items()
        ])

        # Iterate over items in trakt list
        t_items = t_list.items()

        if t_items is None:
            log.warn('Unable to retrieve list items for: %r', t_list)
            return

        for t_item in t_items:
            media = self.get_media(t_item)

            if media is None:
                continue

            p_keys = self.current.map.by_guid(t_item.pk)

            if not p_keys:
                # Item not found in plex
                continue

            # Convert to list (for indexing)
            p_keys = list(p_keys)

            # Use first match found in plex
            p_section_key, p_item_key = p_keys[0]

            # Retrieve section UUID
            p_section_uuid = p_sections_map.get(p_section_key)

            # Build URI
            uri = 'library://%s/item/%s' % (
                p_section_uuid,
                urllib.quote_plus('/library/metadata/%s' % p_item_key)
            )

            # Execute handler
            self.execute_handlers(
                media, SyncData.ListLiked,

                playlist=playlist,
                playlist_items=playlist_items,

                t_item=t_item,

                p_keys=p_keys,
                uri=uri
            )

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

    def get_playlist(self, p_playlists, t_list):
        if not p_playlists or not t_list:
            return None

        # Try find existing playlist
        p_playlist = p_playlists.get(t_list.name.lower())

        if p_playlist:
            return p_playlist

        # Create new playlist
        log.debug('Creating new playlist %r for account %r', t_list.name, self.current.account.id)

        return Plex['playlists'].create(
            type='video',
            title=t_list.name,
            uri='trakt://list/%s/%s' % (self.current.account.id, t_list.id)
        ).first()
