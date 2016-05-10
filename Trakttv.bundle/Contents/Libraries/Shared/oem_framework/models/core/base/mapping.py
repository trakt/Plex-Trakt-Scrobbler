from oem_framework.models.core.base.model import Model


class BaseMapping(Model):
    __slots__ = ['collection']

    def __init__(self, collection):
        self.collection = collection

    def to_dict(self, key=None):
        raise NotImplementedError
