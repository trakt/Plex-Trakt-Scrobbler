from plex.objects.core.base import Property
from plex.objects.library.extra.guid import Guid
from plex.objects.library.container import ChildrenContainer
from plex.objects.library.metadata.show import Show
from plex.objects.library.metadata.base import Metadata
from plex.objects.library.video import Directory
from plex.objects.mixins.rate import RateMixin


class Season(Directory, Metadata, RateMixin):
    show = Property(resolver=lambda: Season.construct_show)

    index = Property(type=int)

    guids = Property(resolver=lambda: Guid.from_node)
    agent_guid = Property('guid')
    
    @property
    def guid(self):
        try:
            return self.guids[0].id
        except:
            return self.agent_guid

    banner = Property
    theme = Property

    episode_count = Property('leafCount', int)
    viewed_episode_count = Property('viewedLeafCount', int)

    view_count = Property('viewCount', int)

    def children(self):
        return self.client['library/metadata'].children(self.rating_key)

    def __repr__(self):
        if self.show:
            return '<Season %r (%s) - S%02d>' % (self.show.title, self.show.year, self.index)

        return '<Season S%02d>' % self.index

    @staticmethod
    def construct_show(client, node):
        attribute_map = {
            'index'    : 'parentIndex',
            'key'      : 'parentKey',
            'ratingKey': 'parentRatingKey',

            'title'    : 'parentTitle',
            'summary'  : 'parentSummary',
            'thumb'    : 'parentThumb',

            'theme'    : 'parentTheme'
        }

        return Show.construct(client, node, attribute_map, child=True)


class SeasonChildrenContainer(ChildrenContainer):
    show = Property(resolver=lambda: SeasonChildrenContainer.construct_show)
    season = Property(resolver=lambda: SeasonChildrenContainer.construct_season)

    key = Property

    banner = Property
    theme = Property

    @staticmethod
    def construct_show(client, node):
        attribute_map = {
            'ratingKey'    : 'grandparentRatingKey',

            'title'        : 'grandparentTitle',

            'contentRating': 'grandparentContentRating',
            'studio'       : 'grandparentStudio',

            'theme'        : 'grandparentTheme',
            'thumb'        : 'grandparentThumb'
        }

        return Show.construct(client, node, attribute_map, child=True)

    @staticmethod
    def construct_season(client, node):
        attribute_map = {
            'index': 'parentIndex',
            'title': 'parentTitle'
        }

        return Season.construct(client, node, attribute_map, child=True)

    def __iter__(self):
        for item in super(ChildrenContainer, self).__iter__():
            item.show = self.show
            item.season = self.season

            yield item
