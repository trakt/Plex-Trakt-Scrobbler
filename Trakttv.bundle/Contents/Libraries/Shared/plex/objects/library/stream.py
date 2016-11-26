from plex.objects.core.base import Descriptor, Property


class Stream(Descriptor):
    id = Property(type=int)
    index = Property(type=int)

    stream_type = Property('streamType', int)
    selected = Property(type=bool)

    title = Property
    duration = Property(type=(float, int))

    language = Property
    language_code = Property('languageCode')

    codec = Property
    codec_id = Property('codecID')

    bit_depth = Property('bitDepth', int)
    chroma_subsampling = Property('chromaSubsampling')
    color_space = Property('colorSpace')

    width = Property(type=int)
    height = Property(type=int)

    bitrate = Property(type=int)
    bitrate_mode = Property('bitrateMode')

    channels = Property(type=int)
    sampling_rate = Property('samplingRate', int)

    frame_rate = Property('frameRate')
    profile = Property
    scan_type = Property('scanType')

    bvop = Property(type=int)
    gmc = Property(type=int)
    level = Property
    qpel = Property(type=int)

    @classmethod
    def from_node(cls, client, node):
        items = []

        for genre in cls.helpers.findall(node, 'Stream'):
            _, obj = Stream.construct(client, genre, child=True)

            items.append(obj)

        return [], items
