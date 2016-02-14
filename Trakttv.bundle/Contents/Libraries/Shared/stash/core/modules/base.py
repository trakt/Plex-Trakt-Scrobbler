from stash.core.modules.manager import ModuleManager
from stash.lib import six

from abc import ABCMeta
from collections import MutableMapping


class ModuleMeta(type):
    def __init__(cls, *args, **kwargs):
        if not cls.__module__.endswith('.base'):
            ModuleManager.register(cls)

        super(ModuleMeta, cls).__init__(*args, **kwargs)


class Module(six.with_metaclass(ModuleMeta)):
    __group__ = None
    __key__ = None

    def __init__(self):
        self.stash = None

    @property
    def key_encode(self):
        encode, _ = self.stash.key_transform

        return encode

    @property
    def key_decode(self):
        _, decode = self.stash.key_transform

        return decode


class MappingMeta(ModuleMeta, ABCMeta):
    pass


class MappingModule(six.with_metaclass(MappingMeta, Module, MutableMapping)):
    pass
