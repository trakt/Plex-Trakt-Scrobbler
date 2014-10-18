from plex.objects.core.base import Descriptor, Property


class Director(Descriptor):
    id = Property(type=int)
    tag = Property

    @classmethod
    def from_node(cls, client, node):
        return cls.construct(client, node.find('Director'), child=True)
