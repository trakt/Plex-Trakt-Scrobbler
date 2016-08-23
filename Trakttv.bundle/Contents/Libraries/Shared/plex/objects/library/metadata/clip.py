from plex.objects.core.base import Property
from plex.objects.library.metadata.base import Metadata
from plex.objects.library.metadata.photo import PhotoAlbum
from plex.objects.library.video import Video


class Clip(Video, Metadata):
    grandparent = Property(resolver=lambda: Clip.construct_grandparent)
    parent = Property(resolver=lambda: Clip.construct_parent)

    extra_type = Property('extraType', int)

    index = Property(type=int)

    filename = Property
    device = Property

    def __repr__(self):
        if self.grandparent and self.parent:
            return '<Clip %r - %r - %r>' % (
                self.grandparent.title,
                self.parent.title,
                self.title
            )

        if self.grandparent:
            return '<Clip %r - %r>' % (
                self.grandparent.title,
                self.title
            )

        if self.parent:
            return '<Clip %r - %r>' % (
                self.parent.title,
                self.title
            )

        return '<Clip %r>' % self.title

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
