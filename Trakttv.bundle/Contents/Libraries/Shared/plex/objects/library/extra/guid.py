from plex.objects.core.base import Descriptor, Property


class Guid(Descriptor):
    id = Property(type=str)

    @classmethod
    def from_node(cls, client, node):
        return cls.construct(client, cls.helpers.find(node, 'Guid'), child=True)
