from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.metadata.album import Album
from plex.objects.library.metadata.artist import Artist
from plex.objects.library.metadata.base import Metadata
from plex.objects.mixins.playlist_item import PlaylistItemMixin
from plex.objects.mixins.rate import RateMixin
from plex.objects.mixins.scrobble import ScrobbleMixin
from plex.objects.mixins.session import SessionMixin


class Track(Directory, Metadata, PlaylistItemMixin, RateMixin, SessionMixin, ScrobbleMixin):
    artist = Property(resolver=lambda: Track.construct_artist)
    album = Property(resolver=lambda: Track.construct_album)

    index = Property(type=int)

    view_count = Property('viewCount', int)
    view_offset = Property('viewOffset', int)

    duration = Property(type=int)

    chapter_source = Property('chapterSource')

    def __repr__(self):
        if self.artist:
            return '<Track %r - %r>' % (
                self.artist.title,
                self.title
            )
        elif self.album:
            return '<Track %r (%s) - %r>' % (
                self.album.title,
                self.album.year,

                self.title
            )

        return '<Track %r>' % self.title

    @staticmethod
    def construct_artist(client, node):
        attribute_map = {
            'key':          'grandparentKey',
            'ratingKey':    'grandparentRatingKey',

            'title':        'grandparentTitle',

            'art':          'grandparentArt',
            'thumb':        'grandparentThumb'
        }

        return Artist.construct(client, node, attribute_map, child=True)

    @staticmethod
    def construct_album(client, node):
        attribute_map = {
            'index':        'parentIndex',
            'key':          'parentKey',
            'ratingKey':    'parentRatingKey',

            'title':        'parentTitle',
            'year':         'parentYear',

            'thumb':        'parentThumb'
        }

        return Album.construct(client, node, attribute_map, child=True)
