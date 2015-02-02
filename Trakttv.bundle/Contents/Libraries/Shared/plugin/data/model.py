from plugin.core.environment import Environment
from plugin.core.io import FileIO
from plugin.data.cache import DataCache

import jsonpickle
import logging
import os

log = logging.getLogger(__name__)

cache = DataCache()


class Property(object):
    def __init__(self, value_or_func=None, pickle=True):
        self.pickle = pickle

        self.func = None
        self.value_ = None

        # Set relevant attribute from `value_or_func` parameter
        if hasattr(value_or_func, '__call__'):
            self.func = value_or_func
        else:
            self.value_ = value_or_func

    @property
    def value(self):
        try:
            if self.func:
                return self.func()

            return self.value_
        except Exception, ex:
            log.error('Property - unable to resolve value (func: %r) - %s', func, ex)
            return None


class Model(object):
    group = None

    def __init__(self, key):
        self.key = key

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls, *args, **kwargs)

        # Set default values
        cls.set_defaults(obj)

        return obj

    def save(self):
        if not self.group:
            raise ValueError()

        # Save to memory cache
        cache[self.group][self.key] = self

        # Save to disk
        if not os.path.exists(self.group_path()):
            os.makedirs(self.group_path())

        FileIO.write(self.item_path(self.key), jsonpickle.encode(self))

    @classmethod
    def all(cls, filter=None):
        if not cls.group or not os.path.exists(cls.group_path()):
            return []

        items = []

        for name in os.listdir(cls.group_path()):
            key, ext = os.path.splitext(name)

            if ext != '.json':
                continue

            value = cls.load(key)

            if filter and not filter(value):
                continue

            items.append((key, value))

        return items

    @classmethod
    def load(cls, key):
        if not cls.group:
            raise ValueError()

        # Try retrieve from memory cache
        item = cache[cls.group].get(key)

        if item:
            # Return `item` from cache
            return item

        # Otherwise, try retrieve from disk
        if not os.path.exists(cls.group_path()):
            os.makedirs(cls.group_path())

        path = cls.item_path(key)

        if not FileIO.exists(path):
            return None

        # Load data from disk
        try:
            data = FileIO.read(path)
        except Exception, ex:
            log.warn('Unable to load "%s" (%s)', path, ex)
            return None

        # Decode data with jsonpickle
        item = cls.decode(data)

        if item is None:
            log.warn('Unable to decode item at "%s"', path)
            return None

        # Cache item in memory
        cache[cls.group][key] = item

        return item

    @classmethod
    def decode(cls, data):
        try:
            # Decode object from data
            obj = jsonpickle.decode(data)
        except Exception, ex:
            log.warn('Unable to decode data with jsonpickle - %s', ex)
            return None

        # Set default values
        cls.set_defaults(obj)

        return obj

    @classmethod
    def set_defaults(cls, obj):
        # Construct properties
        for key in vars(cls):
            prop = getattr(cls, key)

            if type(prop) is not Property:
                # Not a valid class property
                continue

            # Get current value
            value = getattr(obj, key, None)

            if type(value) is not Property:
                # Value already set
                continue

            # Set default value
            setattr(obj, key, prop.value)

        return obj

    def delete(self):
        if not self.group:
            raise ValueError()

        # Delete from memory cache
        cache[self.group].delete(self.key)

        # Delete from disk
        if not os.path.exists(self.group_path()):
            os.makedirs(self.group_path())

        path = self.item_path(self.key)

        if not FileIO.exists(path):
            return

        FileIO.delete(path)

    def __getstate__(self):
        state = {}

        for key, value in self.__dict__.items():
            # Try lookup class property for attribute
            prop = getattr(self.__class__, key, None)

            # Ignore attributes that have been marked at `pickle=False`
            if prop and not prop.pickle:
                continue

            # Store attribute in `state`
            state[key] = value

        return state

    @classmethod
    def group_path(cls):
        return os.path.join(Environment.path.plugin_data, cls.group)

    @classmethod
    def item_path(cls, key):
        if type(key) is tuple:
            key = '.'.join(key)

        return os.path.join(cls.group_path(), '%s.json' % key)
