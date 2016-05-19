import logging

log = logging.getLogger(__name__)


class ModelRegistryMeta(type):
    _models = {}

    def __getitem__(self, key):
        return self._models[key]


class ModelRegistry(object):
    __metaclass__ = ModelRegistryMeta

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
