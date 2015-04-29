from plugin.core.helpers.variable import to_tuple
from plugin.models import db

import apsw
import inspect
import logging

log = logging.getLogger(__name__)


class Method(object):
    def __init__(self, manager, *args, **kwargs):
        self.manager = manager

    @property
    def model(self):
        return self.manager.model


class Get(Method):
    def __call__(self, *query):
        return self.model.get(*query)

    def all(self):
        return self.model.select()

    def by_id(self, id):
        return self(self.model.id == id)

    def or_create(self, *query, **kwargs):
        try:
            return self.manager.create(**kwargs)
        except apsw.ConstraintError, ex:
            pass

        return self(*query)


class Create(Method):
    def __call__(self, **kwargs):
        if not self.model:
            raise Exception('Manager %r has no "model" attribute defined' % self.manager)

        with db.transaction():
            return self.model.create(**kwargs)


class Update(Method):
    def __call__(self, obj, data, save=True):
        changed = False

        for key, value in data.items():
            if not hasattr(obj, key):
                raise KeyError('%r has no key %r' % (obj, key))

            if getattr(obj, key) == value:
                continue

            changed = True
            setattr(obj, key, value)

        if not changed:
            return False

        if save:
            obj.save()

        return True


class ManagerMeta(type):
    def __init__(cls, name, bases, attributes):
        super(ManagerMeta, cls).__init__(name, bases, attributes)

        if '__metaclass__' in attributes:
            return

        # Construct manager methods
        for key in ['get', 'create', 'update']:
            value = getattr(cls, key)

            if not value or not inspect.isclass(value):
                continue

            log.debug('Constructing manager method %r for %r', value, cls)

            # Construct method
            setattr(cls, key, value(cls))


class Manager(object):
    __metaclass__ = ManagerMeta

    create = Create
    get = Get
    update = Update

    model = None
