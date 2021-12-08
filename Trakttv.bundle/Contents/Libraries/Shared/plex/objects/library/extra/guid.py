from plex.objects.core.base import Descriptor, Property


class Guid(Descriptor):
    id = Property(type=str)

    @classmethod
    def from_node(cls, client, node):
        items = []
        
        for guid in cls.helpers.findall(node, 'Guid'):
            _, obj = Guid.construct(client, guid, child=True)
            
            items.append(obj)
        
        return [], items
