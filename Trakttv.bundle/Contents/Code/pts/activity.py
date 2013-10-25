from core.eventing import EventHandler


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


class PlexActivity(object):
    available_methods = []
    current_method = None

    on_update_collection = EventHandler()

    @classmethod
    def register(cls, method, weight=1):
        cls.available_methods.append((weight, method))

    @classmethod
    def update_collection(cls, item_id, action):
        cls.on_update_collection.fire(item_id, action)

    @classmethod
    def test(cls):
        # Sort available methods by weight first
        cls.available_methods = sorted(cls.available_methods, key=lambda x: x[0], reverse=True)

        # Test methods until an available method is found
        for weight, method in cls.available_methods:
            if method.test():
                cls.current_method = method(cls)
                Log.Info('Picked method %s' % cls.current_method.name)
                break
            else:
                Log.Info('%s method not available' % method.name)

        if not cls.current_method:
            Log.Warn('No method available to determine now playing status, auto-scrobbling not available.')
            return False

        return True

    @classmethod
    def run(cls):
        if not cls.current_method:
            return

        cls.current_method.run()
