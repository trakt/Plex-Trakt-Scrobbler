from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.container import MediaContainer
from plex.objects.library.metadata.base import Metadata
from plex.objects.library.metadata.artist import Artist
from plex.objects.mixins.rate import RateMixin


class Album(Directory, Metadata, RateMixin):
    artist = Property(resolver=lambda: Album.construct_artist)

    index = Property(type=int)

    year = Property(type=int)
    originally_available_at = Property('originallyAvailableAt')

    track_count = Property('leafCount', int)
    viewed_track_count = Property('viewedLeafCount', int)

    def children(self):
        response = self.http.get('children')

        return self.parse(response, {
            'MediaContainer': (TrackContainer, {
                'Track': 'Track'
            })
        })

    @staticmethod
    def construct_artist(client, node):
        attribute_map = {
            'key':          'parentKey',
            'ratingKey':    'parentRatingKey',

            'title':        'parentTitle',
            'thumb':        'parentThumb'
        }

        return Artist.construct(client, node, attribute_map, child=True)


class TrackContainer(MediaContainer, Album):
    artist = Property(resolver=lambda: TrackContainer.construct_artist)

    attribute_map = {
        'index':            'parentIndex',
        'title':            'parentTitle',
        'year':             'parentYear',
        '*':                '*'
    }

    @staticmethod
    def construct_artist(client, node):
        attribute_map = {
            'title':        'grandparentTitle'
        }

        return Artist.construct(client, node, attribute_map, child=True)
