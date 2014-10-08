from plex.objects.core.base import Descriptor, Property
from plex.objects.library.part import Part


class Media(Descriptor):
    parts = Property(resolver=lambda: Media.construct_parts)

    id = Property(type=int)

    video_codec = Property('videoCodec')
    video_frame_rate = Property('videoFrameRate')
    video_resolution = Property('videoResolution')

    audio_channels = Property('audioChannels', type=int)
    audio_codec = Property('audioCodec')

    container = Property

    width = Property(type=int)
    height = Property(type=int)

    aspect_ratio = Property('aspectRatio', type=float)
    bitrate = Property(type=int)
    duration = Property(type=int)

    @staticmethod
    def construct_parts(client, node):
        items = []

        for part in node.findall('Part'):
            _, obj = Part.construct(client, part, child=True)

            items.append(obj)

        return [], items
