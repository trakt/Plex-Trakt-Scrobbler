from plex.objects.core.base import Descriptor, Property


class Country(Descriptor):
    id = Property(type=int)
    tag = Property

    @classmethod
    def from_node(cls, client, node):
        return cls.construct(client, node.find('Country'), child=True)
