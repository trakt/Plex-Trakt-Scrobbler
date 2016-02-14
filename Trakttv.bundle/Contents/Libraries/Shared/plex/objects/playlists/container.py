from plex.objects.core.base import Property
from plex.objects.library.container import MediaContainer


class PlaylistItemContainer(MediaContainer):
    title = Property

    duration = Property(type=int)
    smart = Property(type=(int, bool))

    leaf_count = Property('leafCount', int)
