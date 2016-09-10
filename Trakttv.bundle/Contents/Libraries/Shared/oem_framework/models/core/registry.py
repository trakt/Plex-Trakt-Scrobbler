import logging
import six

log = logging.getLogger(__name__)


class ModelRegistryMeta(type):
    _models = {}

    def __getitem__(self, key):
        return self._models[key]


@six.add_metaclass(ModelRegistryMeta)
class ModelRegistry(object):
    @classmethod
    def get(cls, name, default=None):
        return cls._models.get(name, default)

    @classmethod
    def register(cls, model):
        replaced = model.__name__ in cls._models

        cls._models[model.__name__] = model

        if replaced:
            log.debug('[%-14s] Replaced: %r', model.__name__, model)
        else:
            log.debug('[%-14s] Registered: %r', model.__name__, model)
