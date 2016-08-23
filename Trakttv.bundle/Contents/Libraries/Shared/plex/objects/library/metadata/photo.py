from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.metadata.base import Metadata
from plex.objects.mixins.session import SessionMixin


class PhotoAlbum(Directory, Metadata):
    index = Property(type=int)

    def __repr__(self):
        return '<PhotoAlbum %r>' % self.title


class Photo(Directory, Metadata, SessionMixin):
    grandparent = Property(resolver=lambda: Photo.construct_grandparent)
    parent = Property(resolver=lambda: Photo.construct_parent)

    index = Property(type=int)

    filename = Property
    device = Property

    view_offset = Property('viewOffset', int)

    @property
    def album(self):
        return self.parent

    def __repr__(self):
        if self.grandparent and self.parent:
            return '<Photo %r - %r - %r>' % (
                self.grandparent.title,
                self.parent.title,
                self.title
            )

        if self.grandparent:
            return '<Photo %r - %r>' % (
                self.grandparent.title,
                self.title
            )

        if self.parent:
            return '<Photo %r - %r>' % (
                self.parent.title,
                self.title
            )

        return '<Photo %r>' % self.title

    @staticmethod
    def construct_grandparent(client, node):
        attribute_map = {
            'key':          'grandparentKey',
            'ratingKey':    'grandparentRatingKey',
            'index':        'grandparentIndex',

            'title':        'grandparentTitle',

            'art':          'grandparentArt',
            'thumb':        'grandparentThumb'
        }

        return PhotoAlbum.construct(client, node, attribute_map, child=True)

    @staticmethod
    def construct_parent(client, node):
        attribute_map = {
            'key':          'parentKey',
            'ratingKey':    'parentRatingKey',
            'index':        'parentIndex',

            'title':        'parentTitle',

            'art':          'parentArt',
            'thumb':        'parentThumb'
        }

        return PhotoAlbum.construct(client, node, attribute_map, child=True)
