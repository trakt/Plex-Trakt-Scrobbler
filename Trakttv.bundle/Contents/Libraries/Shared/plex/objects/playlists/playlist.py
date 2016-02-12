from plex import Plex
from plex.objects.core.base import Descriptor, Property


class Playlist(Descriptor):
    composite = Property
    key = Property

    type = Property
    playlist_type = Property('playlistType')

    guid = Property
    rating_key = Property('ratingKey')

    title = Property
    title_sort = Property('titleSort')
    summary = Property

    duration = Property(type=int)
    duration_seconds = Property('durationInSeconds', int)

    view_count = Property('viewCount', int)

    leaf_count = Property('leafCount', int)
    smart = Property(type=(int, bool))

    added_at = Property('addedAt', int)
    last_viewed_at = Property('lastViewedAt', int)
    updated_at = Property('updatedAt', int)

    def add(self, item_uri):
        return Plex['playlists/*/items'].add(
            self.rating_key,

            item_uri=item_uri
        )

    def delete(self):
        return Plex['playlists'].delete(
            self.rating_key
        )

    def items(self, include_related=None, start=None, size=None):
        return Plex['playlists/*/items'].all(
            self.rating_key,

            include_related=include_related,
            start=start,
            size=size
        )

    def move(self, item_id, after=None):
        return Plex['playlists/*/items'].move(
            self.rating_key,

            item_id=item_id,
            after=after
        )

    def remove(self, item_id):
        return Plex['playlists/*/items'].remove(
            self.rating_key,

            item_id=item_id
        )

    def update(self, title=None, summary=None):
        return Plex['library/metadata'].update(
            self.rating_key,

            title=title,
            summary=summary
        )
