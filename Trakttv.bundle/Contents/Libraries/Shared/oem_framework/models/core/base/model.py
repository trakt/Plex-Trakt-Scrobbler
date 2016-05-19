from oem_framework.models.core.registry import ModelRegistry

import logging

log = logging.getLogger(__name__)


class ModelMeta(type):
    def __new__(mcs, name, parents, dct):
        cls = super(ModelMeta, mcs).__new__(mcs, name, parents, dct)

        ModelRegistry.register(cls)
        return cls


class Model(object):
    __metaclass__ = ModelMeta

    __protocols__ = None
    __wrapper__ = False

    @classmethod
    def set_protocol(cls, key, protocol):
        if cls.__protocols__ is None:
            cls.__protocols__ = {}

        cls.__protocols__[key] = protocol

    @classmethod
    def from_dict(cls, collection, data, **kwargs):
        raise NotImplementedError

    def to_dict(self, **kwargs):
        raise NotImplementedError

    def __eq__(self, other):
        if not isinstance(other, Model):
            return False

        return self.to_dict() == other.to_dict()
