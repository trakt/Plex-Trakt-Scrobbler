from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.metadata.base import Metadata
from plex.objects.mixins.session import SessionMixin


class PhotoAlbum(Directory, Metadata):
    index = Property(type=int)

    def __repr__(self):
        return '<PhotoAlbum %r>' % self.title


class Photo(Directory, Metadata, SessionMixin):
    album = Property(resolver=lambda: Photo.construct_album)

    index = Property(type=int)

    def __repr__(self):
        return '<Photo %r>' % self.title

    @staticmethod
    def construct_album(client, node):
        attribute_map = {
            'key':          'parentKey',
            'ratingKey':    'parentRatingKey',
            'index':        'parentIndex',

            'title':        'parentTitle',

            'thumb':        'parentThumb'
        }

        return PhotoAlbum.construct(client, node, attribute_map, child=True)
