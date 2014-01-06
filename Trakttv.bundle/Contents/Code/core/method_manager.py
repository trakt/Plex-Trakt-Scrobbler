from core.logger import Logger
import threading

log = Logger('core.method_manager')


class Method(object):
    name = None

    def __init__(self):
        self.thread = threading.Thread(target=self.run, name=self.get_name())
        self.running = False

    def get_name(self):
        return self.name

    @classmethod
    def test(cls):
        raise NotImplementedError()

    def start(self):
        if self.running:
            return

        self.thread.start()

    def run(self):
        raise NotImplementedError()


class Manager(object):
    available = []
    enabled = []

    @classmethod
    def register(cls, method, weight=None):
        item = (weight, method)

        # weight = None, highest priority
        if weight is None:
            cls.available.insert(0, item)
            return

        # insert in DESC order
        for x in xrange(len(cls.available)):
            w, _ = cls.available[x]

            if w is not None and w < weight:
                cls.available.insert(x, item)
                return

        # otherwise append
        cls.available.append(item)

    @classmethod
    def test(cls):
        # Test methods until an available method is found
        for weight, method in cls.available:
            if method.test():
                cls.enabled.append(method(cls))

                if not Prefs['force_legacy']:
                    break
            elif weight is None:
                cls.enabled.append(method(cls))
            else:
                log.info('%s method not available' % method.name)

        if cls.enabled:
            log.info('Enabled methods: %s' % ', '.join([x.name for x in cls.enabled]))
            return True

        log.error('No activity methods available, unable to start.')
        return False

    @classmethod
    def start(cls):
        if not cls.test() or not cls.enabled:
            return

        for method in cls.enabled:
            method.start()
