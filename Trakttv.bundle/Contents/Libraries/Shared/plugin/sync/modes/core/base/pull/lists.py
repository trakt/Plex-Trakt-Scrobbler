from plugin.sync.core.enums import SyncMedia
from plugin.sync.modes.core.base.mode import Mode

from plex import Plex
import logging
import trakt.objects

log = logging.getLogger(__name__)


class PullListsMode(Mode):
    @staticmethod
    def get_media(t_item):
        if not t_item:
            return None

        t_type = type(t_item)

        if t_type is trakt.objects.Movie:
            return SyncMedia.Movies

        if t_type is trakt.objects.Show:
            return SyncMedia.Shows

        if t_type is trakt.objects.Season:
            return SyncMedia.Seasons

        if t_type is trakt.objects.Episode:
            return SyncMedia.Episodes

        log.warn('Unknown "t_item" type: %r', t_type)
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

    def get_items(self, data, media):
        for m in media:
            # Retrieve trakt watchlist items from cache
            t_items = self.trakt[(m, data)]

            if t_items is None:
                log.warn('Unable to retrieve items for %r watchlist', m)
                continue

            for item in t_items.itervalues():
                for t_item in self.expand_items(m, item):
                    yield t_item

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

    @classmethod
    def expand(cls, p_items, t_items):
        p_type = type(p_items)
        t_type = type(t_items)

        if p_type is not dict and t_type is not dict:
            return [(p_items, t_items)]

        result = []

        if p_type is dict and t_type is dict:
            # Match items by key
            for key, t_item in t_items.iteritems():
                result.extend(cls.expand(p_items.get(key), t_item))
        elif p_type is dict:
            # Iterate over plex items
            for p_item in p_items.itervalues():
                result.extend(cls.expand(p_item, t_items))
        elif t_type is dict:
            # Iterate over trakt items
            for t_item in t_items.itervalues():
                result.extend(cls.expand(p_items, t_item))
        else:
            log.warn('Unsupported items (p_items: %r, t_items: %r)', p_items, t_items)

        return result

    @staticmethod
    def expand_items(media, item):
        if media in [SyncMedia.Movies, SyncMedia.Shows]:
            yield item
        elif media == SyncMedia.Seasons:
            # Yield each season in show
            for t_season in item.seasons.itervalues():
                yield t_season
        elif media == SyncMedia.Episodes:
            # Iterate over each season in show
            for t_season in item.seasons.itervalues():
                # Yield each episode in season
                for t_episode in t_season.episodes.itervalues():
                    yield t_episode

    @staticmethod
    def format_changes(changes):
        for key, actions in changes.items():
            # Build key
            key = list(key)
            key = '/'.join([str(x) for x in key])

            yield '    [%-16s] actions: %r' % (
                key, actions
            )

    @staticmethod
    def format_mapper_result(items):
        for key, index, (p_index, p_item), (t_index, t_item) in items:
            # Build key
            key = list(key)
            key[0] = '/'.join(key[0])

            key = '/'.join([str(x) for x in key])

            # Build indices
            if p_index is None:
                p_index = '---'

            if t_index is None:
                t_index = '---'

            yield '    [%-16s](%3s) - %68s <[%3s] - [%3s]> %r' % (
                key, index,
                p_item, p_index,
                t_index, t_item
            )
