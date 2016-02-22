from plex.objects.core.base import Property
from plex.objects.library.container import MediaContainer


class PlaylistItemContainer(MediaContainer):
    rating_key = Property('ratingKey')

    title = Property

    duration = Property(type=int)
    smart = Property(type=(int, bool))

    composite = Property
    playlist_type = Property('playlistType')

    leaf_count = Property('leafCount', int)
