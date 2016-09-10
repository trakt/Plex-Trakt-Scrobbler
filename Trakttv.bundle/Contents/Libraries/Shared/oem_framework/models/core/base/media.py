from oem_framework.core.helpers import convert_keys_to_string
from oem_framework.models.core.base.mapping import BaseMapping
from oem_framework.models.core.base.model import Model
from oem_framework.models.core.mixins.names import NamesMixin

from bencode import bencode
import collections
import hashlib
import inspect
import logging
import six

log = logging.getLogger(__name__)

BASE_ATTRIBUTES = ['identifiers', 'supplemental', 'parameters']


class BaseMedia(Model, NamesMixin):
    __slots__ = ['collection', 'media', 'identifiers', 'supplemental', 'parameters']
    __attributes__ = None

    def __init__(self, collection, media, identifiers=None, supplemental=None, **parameters):
        self.collection = collection
        self.media = media

        self.identifiers = identifiers or {}
        self.supplemental = supplemental or {}
        self.parameters = dict([
            (key, value) for key, value in parameters.items()
            if value is not None and value != ""
        ]) if parameters else {}

    @property
    def format(self):
        return self.collection.storage.format

    def hash(self):
        # Convert object to bencode
        data = self.to_bencode(flatten=False)

        if six.PY3:
            data = data.encode('utf-8')

        # Calculate hash of bencode string
        m = hashlib.md5()
        m.update(data)

        # Return hash
        if self.format.__supports_binary__:
            return m.digest()

        return m.hexdigest()

    def to_bencode(self, flatten=True):
        # Convert object to dictionary
        data = self.to_dict(
            flatten=flatten
        )

        # Ensure dictionary keys are strings
        data = convert_keys_to_string(data)

        # Encode `data` to a bencode string
        try:
            return bencode(data)
        except Exception as ex:
            log.warn('Unable to encode object to bencode: %s', ex, exc_info=True)
            return None

    def to_dict(self, key=None, flatten=True):
        result = {}

        classes = [
            cls for cls in inspect.getmro(self.__class__)
            if issubclass(cls, BaseMedia)
        ]

        for cls in classes:
            # Retrieve class attributes
            if cls is BaseMedia:
                attributes = BASE_ATTRIBUTES
            else:
                attributes = cls.__attributes__

            # Ensure attributes have been defined
            if attributes is None:
                log.warn('No attributes defined for %r', cls)
                continue

            # Add attributes from each class
            for k in attributes:
                v = getattr(self, k)

                # Flatten value
                v = self._flatten(v, flatten=flatten)

                # Ignore empty attributes
                if v is None:
                    continue

                # Update `result` dictionary
                result[k] = v

        return result

    def matches_identifiers(self, identifiers):
        for service, key_a in identifiers.items():
            if service not in self.identifiers:
                return False

            key_b = self.identifiers[service]

            if type(key_a) is list and type(key_b) is list:
                # Ensure all the keys in `key_b` are in `key_a`
                if set(key_b) - set(key_a):
                    return False
            elif type(key_a) is list:
                # Not supported
                return False
            elif type(key_b) is list:
                # Ensure `key_b` is in `key_a`
                if key_a not in key_b:
                    return False
            elif key_a != key_b:
                return False

        return True

    @classmethod
    def _flatten(cls, value, key=None, flatten=True):
        if isinstance(value, six.string_types + (int,)):
            return value

        if isinstance(value, BaseMapping):
            return value.to_dict(key=key, flatten=flatten)

        if isinstance(value, BaseMedia):
            return value.to_dict(key=key, flatten=flatten)

        if isinstance(value, Model):
            return value.to_dict()

        if isinstance(value, collections.Mapping):
            if len(value) < 1:
                return None

            def iterator():
                for k, v in value.items():
                    v = cls._flatten(v, key=k, flatten=flatten)

                    if v is None:
                        continue

                    yield k, v

            return dict(iterator()) or None

        if isinstance(value, collections.Sized):
            if len(value) < 1:
                return None

            def iterator():
                for v in value:
                    if v is value:
                        raise NotImplementedError

                    v = cls._flatten(v, flatten=flatten)

                    if v is None:
                        continue

                    yield v

            return list(iterator()) or None

        return value
