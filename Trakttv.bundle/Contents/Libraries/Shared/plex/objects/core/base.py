from plex.interfaces.core.base import Interface

import logging
import traceback

log = logging.getLogger(__name__)


class Property(object):
    def __init__(self, name=None, type=None, resolver=None):
        self.name = name
        self.type = type
        self.resolver = resolver

    def value(self, client, key, node, keys_used):
        if self.resolver is not None:
            return self.value_func(client, node, keys_used)

        return self.value_node(key, node, keys_used)

    def value_node(self, key, node, keys_used):
        value = node.get(key)
        keys_used.append(key)

        if value is None:
            return None

        return self.value_convert(value)

    def value_convert(self, value):
        if not self.type:
            return value

        types = self.type if type(self.type) is list else [self.type]
        result = value

        for target_type in types:
            try:
                result = target_type(result)
            except:
                return None

        return result

    def value_func(self, client, node, keys_used):
        func = self.resolver()

        try:
            keys, value = func(client, node)

            keys_used.extend(keys)
            return value
        except Exception, ex:
            log.warn('Exception in value function (%s): %s - %s', func, ex, traceback.format_exc())
            return None


class DescriptorMeta(type):
    def __init__(self, name, bases, attrs):
        super(DescriptorMeta, self).__init__(name, bases, attrs)

        Interface.object_map[self.__name__] = self


class Descriptor(Interface):
    __metaclass__ = DescriptorMeta

    attribute_map = None

    def __init__(self, client, path):
        super(Descriptor, self).__init__(client)
        self.path = path

        self._children = None

    def properties(self):
        keys = [k for k in dir(self) if not k.startswith('_')]

        #log.debug('%s - keys: %s', self, keys)

        for key in keys:
            if key.startswith('_'):
                continue

            value = getattr(self, key)

            if value is Property:
                yield key, Property(key)
            elif isinstance(value, Property):
                yield key, value

    @classmethod
    def construct(cls, client, node, attribute_map=None, path=None, child=False):
        if node is None:
            return [], None

        keys_available = node.keys()
        keys_used = []

        if attribute_map is None:
            attribute_map = cls.attribute_map or {}

        require_map = attribute_map.get('*') != '*'

        # Determine path from object "key"
        key = node.get('key')

        if key is not None:
            path = key[:key.rfind('/')]

        # Construct object
        obj = cls(client, path)

        #log.debug('%s - Properties: %s', cls.__name__, list(obj.properties()))

        for key, prop in obj.properties():
            node_key = prop.name or key

            if attribute_map:
                if node_key in attribute_map:
                    node_key = attribute_map.get(node_key)
                elif require_map:
                    setattr(obj, key, None)
                    continue

            #log.debug('%s - Found property "%s"', cls.__name__, key)
            setattr(obj, key, prop.value(client, node_key, node, keys_used))

        # Post-fill transformation
        obj.__transform__()

        # Look for omitted keys
        omitted = list(set(keys_available) - set(keys_used))
        omitted.sort()

        if omitted and not child:
            log.warn('%s - Omitted attributes: %s', cls.__name__, ', '.join(omitted))

        return keys_used, obj

    def __transform__(self):
        pass

    def __iter__(self):
        return self._children or []


class DescriptorMixin(Descriptor):
    pass
