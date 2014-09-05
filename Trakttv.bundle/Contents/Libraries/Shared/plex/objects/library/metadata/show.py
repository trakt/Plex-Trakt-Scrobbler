from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.container import MediaContainer
from plex.objects.library.metadata.base import Metadata
from plex.objects.mixins.rate import RateMixin


class Show(Directory, Metadata, RateMixin):
    index = Property(type=int)
    duration = Property(type=int)

    studio = Property
    content_rating = Property('contentRating')

    banner = Property
    theme = Property

    year = Property(type=int)
    originally_available_at = Property('originallyAvailableAt')

    episode_count = Property('leafCount', int)
    viewed_episode_count = Property('viewedLeafCount', int)

    def children(self):
        response = self.http.get('children')

        return self.parse(response, {
            'MediaContainer': (SeasonContainer, {
                'Directory': {
                    'season': 'Season'
                }
            })
        })

    def all_leaves(self):
        response = self.http.get('allLeaves')

        return self.parse(response, {
            'MediaContainer': ('EpisodeContainer', {
                'Video': {
                    'episode': 'Episode'
                }
            })
        })


class SeasonContainer(MediaContainer, Show):
    attribute_map = {
        'index':    'parentIndex',
        'title':    'parentTitle',
        'year':     'parentYear',
        '*':        '*'
    }
