from plex.objects.core.base import Descriptor, Property


class Container(Descriptor):
    size = Property(type=int)

    updated_at = Property('updatedAt', int)

    def first(self):
        for item in self:
            return item
