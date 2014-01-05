from core.eventing import EventHandler
from core.logger import Logger
import threading

log = Logger('pts.activity')


class ActivityMethod(object):
    name = None

    on_update_collection = EventHandler()

    def __init__(self, now_playing):
        self.now_playing = now_playing

    @classmethod
    def test(cls):
        return False

    def start(self):
        raise NotImplementedError()

    def update_collection(self, item_id, action):
        self.now_playing.update_collection(item_id, action)


class Activity(object):
    available_methods = []
    enabled_methods = []

    on_update_collection = EventHandler()

    @classmethod
    def register(cls, method, weight=1):
        cls.available_methods.append((weight, method))

    @classmethod
    def update_collection(cls, item_id, action):
        cls.on_update_collection.fire(item_id, action)

    @classmethod
    def test(cls):
        def method_sort_key((weight, _)):
            if weight is None:
                return 1000

            return weight

        # Sort available methods by weight first
        cls.available_methods = sorted(
            cls.available_methods,
            key=method_sort_key,
            reverse=True
        )

        cls.enabled_methods = []

        # Test methods until an available method is found
        for weight, method in cls.available_methods:
            if method.test():
                cls.enabled_methods.append(method(cls))

                if not Prefs['force_legacy']:
                    break
            elif weight is None:
                cls.enabled_methods.append(method(cls))
            else:
                log.info('%s method not available' % method.name)

        if cls.enabled_methods:
            log.info('Enabled methods: %s' % ', '.join([x.name for x in cls.enabled_methods]))
            return True

        log.error('No activity methods available, unable to start.')
        return False

    @classmethod
    def start(cls):
        if not Activity.test() or not cls.enabled_methods:
            return

        for method in cls.enabled_methods:
            method.start()
