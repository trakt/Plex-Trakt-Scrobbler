from plugin.core.helpers.variable import to_tuple
from plugin.models import db

import apsw
import logging

log = logging.getLogger(__name__)


class Manager(object):
    model = None

    @classmethod
    def get_or_create(cls, data, query, fetch=False, update=True, on_create=None):
        query = to_tuple(query)

        name = cls.model.__name__

        try:
            obj = cls.create(**on_create)
            fetch = True
            update = True
        except apsw.ConstraintError:
            obj = cls.get(*query)

        if update:
            cls.update(obj, cls.to_dict(obj, data, fetch=fetch))

        return obj

    @classmethod
    def create(cls, **kwargs):
        with db.transaction():
            return cls.model.create(**kwargs)

    @classmethod
    def get(cls, *query):
        return cls.model.get(*query)

    @classmethod
    def update(cls, obj, data):
        changed = False

        for key, value in data.items():
            if not hasattr(obj, key):
                raise KeyError('%r has no key %r' % (obj, key))

            if getattr(obj, key) == value:
                continue

            changed = True
            setattr(obj, key, value)

        if changed:
            obj.save()
            return True

        return False

    @classmethod
    def to_dict(cls, obj, data, fetch=False):
        raise NotImplementedError()
