from plex.objects.core.base import Property
from plex.objects.library.extra.country import Country
from plex.objects.library.extra.genre import Genre
from plex.objects.library.extra.role import Role
from plex.objects.library.metadata.base import Metadata
from plex.objects.library.video import Video
from plex.objects.mixins.playlist_item import PlaylistItemMixin
from plex.objects.mixins.rate import RateMixin
from plex.objects.mixins.scrobble import ScrobbleMixin


class Movie(Video, Metadata, PlaylistItemMixin, RateMixin, ScrobbleMixin):
    country = Property(resolver=lambda: Country.from_node)
    genres = Property(resolver=lambda: Genre.from_node)
    roles = Property(resolver=lambda: Role.from_node)

    def __repr__(self):
        return '<Movie %r (%s)>' % (self.title, self.year)
