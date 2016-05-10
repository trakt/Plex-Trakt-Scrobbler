from oem_framework.models.core import Model, ModelRegistry


class Item(Model):
    __wrapper__ = True

    @classmethod
    def construct(cls, collection, media, **kwargs):
        return cls.resolve(media)(collection, **kwargs)

    @classmethod
    def from_dict(cls, collection, data, media=None, **kwargs):
        return cls.resolve(media).from_dict(collection, data)

    @classmethod
    def resolve(cls, media):
        if media is None:
            raise ValueError('Invalid value provided for parameter: "media"')

        if media == 'show':
            return ModelRegistry['Show']

        if media == 'movie':
            return ModelRegistry['Movie']

        raise ValueError('Unknown media: %r' % media)
