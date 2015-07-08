from plugin.core.helpers.variable import to_tuple
from plugin.models import db

import apsw
import inspect
import logging
import peewee

log = logging.getLogger(__name__)


class Method(object):
    def __init__(self, manager, *args, **kwargs):
        self.manager = manager

    @property
    def model(self):
        return self.manager.model


class Get(Method):
    def __call__(self, *query, **kwargs):
        obj = self.model.get(*query, **kwargs)

        if obj:
            obj._created = False

        return obj

    def all(self):
        return self.model.select()

    def by_id(self, id):
        return self(self.model.id == id)

    def or_create(self, *query, **kwargs):
        try:
            return self.manager.create(**kwargs)
        except (apsw.ConstraintError, peewee.IntegrityError), ex:
            log.debug('or_create() - ex: %r', ex)

        return self(*query)

    def where(self, *query):
        return self.model.select().where(*query)


class Create(Method):
    def __call__(self, **kwargs):
        if not self.model:
            raise Exception('Manager %r has no "model" attribute defined' % self.manager)

        with db.transaction():
            obj = self.model.create(**kwargs)

        if obj:
            # Set flag
            obj._created = True

        return obj


class Update(Method):
    keys = []

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

    def from_dict(self, obj, changes):
        log.debug('from_dict(%r, %r)', obj, changes)

        if not changes:
            return False

        # Resolve `account`
        if inspect.isfunction(obj):
            obj = obj()

        # Update `TraktAccount`
        data = {}

        for key in self.keys:
            if key not in changes:
                continue

            data[key] = changes[key]

        if data and not self(obj, data):
            log.debug('Unable to update %r (nothing changed?)', obj)

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

            # Construct method
            setattr(cls, key, value(cls))


class Manager(object):
    __metaclass__ = ManagerMeta

    create = Create
    get = Get
    update = Update

    model = None
