from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.container import MediaContainer
from plex.objects.library.metadata.base import Metadata
from plex.objects.mixins.rate import RateMixin


class Artist(Directory, Metadata, RateMixin):
    index = Property(type=int)

    def children(self):
        response = self.http.get('children')

        return self.parse(response, {
            'MediaContainer': (AlbumContainer, {
                'Directory': {
                    'album':    'Album',
                    None:       'Album'  # (All tracks)
                }
            })
        })


class AlbumContainer(MediaContainer, Artist):
    attribute_map = {
        'index':    'parentIndex',
        'title':    'parentTitle',
        '*':        '*'
    }
