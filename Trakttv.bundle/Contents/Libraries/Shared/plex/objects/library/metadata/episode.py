from plex.objects.core.base import Property
from plex.objects.library.metadata.season import Season
from plex.objects.library.metadata.show import Show
from plex.objects.library.metadata.base import Metadata
from plex.objects.library.video import Video
from plex.objects.mixins.playlist_item import PlaylistItemMixin
from plex.objects.mixins.rate import RateMixin
from plex.objects.mixins.scrobble import ScrobbleMixin


class Episode(Video, Metadata, PlaylistItemMixin, RateMixin, ScrobbleMixin):
    show = Property(resolver=lambda: Episode.construct_show)
    season = Property(resolver=lambda: Episode.construct_season)

    index = Property(type=int)
    absolute_index = Property('absoluteIndex', int)

    skip_parent = Property('skipParent', (int, bool))

    def __repr__(self):
        if self.show and self.season:
            return '<Episode %r - S%02dE%02d (%s)>' % (
                self.show.title,

                self.season.index,
                self.index,
                self.year
            )
        elif self.season:
            return '<Episode S%02dE%02d (%s)>' % (
                self.season.index,
                self.index,
                self.year
            )

        return '<Episode E%02d (%s)>' % (
            self.index,
            self.year
        )

    @staticmethod
    def construct_show(client, node):
        attribute_map = {
            'key':          'grandparentKey',
            'ratingKey':    'grandparentRatingKey',

            'title':        'grandparentTitle',

            'art':          'grandparentArt',
            'theme':        'grandparentTheme',
            'thumb':        'grandparentThumb'
        }

        return Show.construct(client, node, attribute_map, child=True)

    @staticmethod
    def construct_season(client, node):
        attribute_map = {
            'index':        'parentIndex',
            'key':          'parentKey',
            'ratingKey':    'parentRatingKey',

            'title':        'parentTitle',

            'thumb':        'parentThumb'
        }

        return Season.construct(client, node, attribute_map, child=True)
