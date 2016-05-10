from oem_framework.models.core import Model


class Range(Model):
    __slots__ = ['collection', 'start', 'end']

    def __init__(self, collection, start=0, end=100):
        self.collection = collection

        self.start = start
        self.end = end

    def is_defined(self):
        return self.start != 0 or self.end != 100

    @classmethod
    def from_dict(cls, collection, data, **kwargs):
        return cls(
            collection,

            start=data.get('start', 0),
            end=data.get('end', 100)
        )

    def to_dict(self):
        result = {}

        if self.start != 0:
            result['start'] = self.start

        if self.end != 100:
            result['end'] = self.end

        return result
