from plugin.api.core.exceptions import ApiError
from plugin.api.core.manager import ApiManager
from plugin.core.helpers import decorator

import logging

log = logging.getLogger(__name__)


class AuthenticationRequiredError(ApiError):
    code = 'authentication.required'
    message = 'API authentication required'


class ServiceMeta(type):
    def __init__(cls, name, bases, attributes):
        super(ServiceMeta, cls).__init__(name, bases, attributes)

        if '__metaclass__' in attributes:
            return

        # Register API service
        ApiManager.register(cls)


class Service(object):
    __metaclass__ = ServiceMeta
    __key__ = None

    manager = None

    def __init__(self, manager):
        self.manager = manager

    @property
    def context(self):
        return self.manager.context


@decorator.wraps
def expose(authenticated=True):
    def outer(func):
        def inner(self, *args, **kwargs):
            if authenticated and self.context.token is None:
                raise AuthenticationRequiredError

            return func(self, *args, **kwargs)

        # Attach meta to wrapper
        inner.__meta__ = {
            'authenticated': authenticated,
            'exposed': True
        }

        return inner

    return outer
