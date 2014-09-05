from plex.objects.core.base import Property
from plex.objects.directory import Directory
from plex.objects.library.extra.director import Director
from plex.objects.library.extra.writer import Writer
from plex.objects.library.media import Media
from plex.objects.mixins.session import SessionMixin


class Video(Directory, SessionMixin):
    director = Property(resolver=lambda: Video.construct_director)
    media = Property(resolver=lambda: Video.construct_media)
    writers = Property(resolver=lambda: Video.construct_writers)

    view_count = Property('viewCount', type=int)
    view_offset = Property('viewOffset', type=int)

    duration = Property(type=int)

    @staticmethod
    def construct_director(client, node):
        return Director.construct(client, node.find('Director'), child=True)

    @staticmethod
    def construct_media(client, node):
        return Media.construct(client, node.find('Media'), child=True)

    @staticmethod
    def construct_writers(client, node):
        items = []

        for writer in node.findall('Writer'):
            _, obj = Writer.construct(client, writer, child=True)

            items.append(obj)

        return [], items

