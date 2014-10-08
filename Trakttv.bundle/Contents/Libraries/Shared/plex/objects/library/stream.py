from plex.objects.core.base import Descriptor, Property


class Stream(Descriptor):
    id = Property(type=int)
    index = Property(type=int)

    stream_type = Property('streamType', type=int)
    selected = Property(type=bool)

    title = Property
    duration = Property(type=int)

    codec = Property
    codec_id = Property('codecID')

    bit_depth = Property('bitDepth', type=int)
    chroma_subsampling = Property('chromaSubsampling')
    color_space = Property('colorSpace')

    width = Property(type=int)
    height = Property(type=int)

    bitrate = Property(type=int)
    bitrate_mode = Property('bitrateMode')

    channels = Property(type=int)
    sampling_rate = Property('samplingRate', type=int)

    frame_rate = Property('frameRate')
    profile = Property
    scan_type = Property('scanType')

    bvop = Property(type=int)
    gmc = Property(type=int)
    level = Property(type=int)
    qpel = Property(type=int)
