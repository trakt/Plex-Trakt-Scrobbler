from plex.objects.core.base import Property, DescriptorMixin


class PlaylistItemMixin(DescriptorMixin):
    playlist_item_id = Property('playlistItemID', int)
