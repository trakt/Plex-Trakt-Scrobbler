from oem_framework.models.core.base.model import Model
from oem_framework.models.core.mixins.names import NamesMixin


class BaseMapping(Model, NamesMixin):
    __slots__ = ['collection']

    def __init__(self, collection):
        self.collection = collection

    def to_dict(self, key=None, flatten=True):
        raise NotImplementedError
