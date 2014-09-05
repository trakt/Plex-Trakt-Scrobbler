from plex.objects.core.base import Descriptor, Property


class Director(Descriptor):
    id = Property(type=int)
    tag = Property
