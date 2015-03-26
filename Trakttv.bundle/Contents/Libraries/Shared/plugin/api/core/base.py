from plugin.api.core.manager import ApiManager


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
