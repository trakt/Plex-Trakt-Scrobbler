from plex.lib import six as six
from plex.interfaces.core.base import Interface

import collections
import logging
import sys
import types

log = logging.getLogger(__name__)


class Property(object):
    helpers = Interface.helpers

    def __init__(self, name=None, type=None, resolver=None):
        self.name = name
        self.type = type
        self.resolver = resolver

    def value(self, descriptor, client, key, node, keys_used):
        if self.resolver is not None:
            return self.value_func(descriptor, client, key, node, keys_used)

        return self.value_node(descriptor, key, node, keys_used)

    def value_node(self, descriptor, key, node, keys_used):
        value = self.helpers.get(node, key)

        if value is None:
            return None

        keys_used.append(key.lower())

        try:
            return self.value_convert(value)
        except Exception as ex:
            log.warn('[%s] Unable to parse property %r - %%s' % (descriptor.__name__, key), ex, exc_info=True)
            return None

    def value_convert(self, value):
        if not self.type:
            return value

        types = self.type if isinstance(self.type, collections.Iterable) else [self.type]
        result = value

        for target_type in types:
            try:
                result = target_type(result)
            except Exception as ex:
                six.reraise(ex, None, sys.exc_info()[2])

        return result

    def value_func(self, descriptor, client, key, node, keys_used):
        func = self.resolver()

        try:
            keys, value = func(client, node)

            keys_used.extend([k.lower() for k in keys])
            return value
        except Exception as ex:
            log.warn('[%s] Exception raised in value function for %r - %%s' % (descriptor.__name__, key), ex, exc_info=True)
            return None


class DescriptorMeta(type):
    def __init__(self, name, bases, attrs):
        super(DescriptorMeta, self).__init__(name, bases, attrs)

        Interface.object_map[self.__name__] = self


@six.add_metaclass(DescriptorMeta)
class Descriptor(Interface):
    attribute_map = None

    def __init__(self, client, path):
        super(Descriptor, self).__init__(client)
        self.path = path

        self._children = None

    @classmethod
    def properties(cls):
        keys = [k for k in dir(cls) if not k.startswith('_')]

        #log.debug('%s - keys: %s', self, keys)

        for key in keys:
            if key.startswith('_'):
                continue

            value = getattr(cls, key)

            if value is Property:
                yield key, Property(key)
            elif isinstance(value, Property):
                yield key, value

    @classmethod
    def construct(cls, client, node, attribute_map=None, path=None, child=False):
        if node is None:
            return [], None

        keys_available = [k.lower() for k in node.keys()]
        keys_used = []

        if attribute_map is None:
            attribute_map = cls.attribute_map or {}

        require_map = attribute_map.get('*') != '*'

        # Determine path from object "key"
        key = cls.helpers.get(node, 'key')

        if key is not None:
            path = key[:key.rfind('/')]

        # Construct object
        obj = cls(client, path)

        #log.debug('%s - Properties: %s', cls.__name__, list(obj.properties()))

        for key, prop in cls.properties():
            node_key = prop.name or key

            if attribute_map:
                if node_key in attribute_map:
                    node_key = attribute_map.get(node_key)
                elif require_map:
                    setattr(obj, key, None)
                    continue

            #log.debug('%s - Found property "%s"', cls.__name__, key)
            setattr(obj, key, prop.value(cls, client, node_key, node, keys_used))

        # Ensure attributes were matched
        if child and not keys_used:
            return [], None

        # Post-fill transformation
        obj.__transform__()

        # Look for omitted keys
        omitted = list(set(keys_available) - set(keys_used))
        omitted.sort()

        if omitted and not child:
            for key in omitted:
                log.warn('[%s] Omitted attribute: %s' % (cls.__name__, key), extra={
                    'event': {
                        'module': __name__,
                        'name': 'construct.omitted_attribute',
                        'key': '%s:%s' % (cls.__name__, key)
                    }
                })

        return keys_used, obj

    def __transform__(self):
        pass

    def __iter__(self):
        return self._children or []

    def __getstate__(self):
        data = self.__dict__

        def build():
            for key, value in data.items():
                if isinstance(value, types.GeneratorType):
                    value = list(value)

                if key in ['client']:
                    continue

                yield key, value

        return dict(build())

    def __str__(self):
        return self.__repr__()


class DescriptorMixin(Descriptor):
    pass
