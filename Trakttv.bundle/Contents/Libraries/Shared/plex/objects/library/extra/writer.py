from plex.objects.core.base import Descriptor, Property


class Writer(Descriptor):
    id = Property(type=int)
    tag = Property
