from plex.objects.core.base import Descriptor, Property
from plex.objects.library.stream import Stream


class Part(Descriptor):
    streams = Property(resolver=lambda: Part.construct_streams)

    id = Property(type=int)
    key = Property

    file = Property
    container = Property

    duration = Property(type=int)
    size = Property(type=int)

    @staticmethod
    def construct_streams(client, node):
        items = []

        for stream in node.findall('Stream'):
            _, obj = Stream.construct(client, stream, child=True)

            items.append(obj)

        return [], items
