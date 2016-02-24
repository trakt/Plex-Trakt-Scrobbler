from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.metadata.base import Metadata


class Photo(Directory, Metadata):
    index = Property(type=int)

    def __repr__(self):
        return '<Photo %r>' % self.title
