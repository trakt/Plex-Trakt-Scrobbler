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

    def scrobble(self, *args, **kwargs):
        # Log.Debug(sessionKey + " - " + state + ' - ' + viewOffset)
        # self.trakt.submit(session_key, state, view_offset)

        raise NotImplementedError()

    def update_collection(self, item_id, action):
        self.now_playing.update_collection(item_id, action)


class PlexActivity(object):
    available_methods = []
    current_method = None

    on_update_collection = EventHandler()

    @classmethod
    def register(cls, method):
        cls.available_methods.append(method)

    @classmethod
    def update_collection(cls, item_id, action):
        cls.on_update_collection.fire(item_id, action)

    @classmethod
    def test(cls):
        for m in cls.available_methods:
            if m.test():
                cls.current_method = m(cls)
                Log.Info('Picked method %s' % cls.current_method.name)
                break

        if not cls.current_method:
            Log.Warn('No method available to determine now playing status, auto-scrobbling not available.')
            return False

        return True

    @classmethod
    def run(cls):
        if not cls.current_method:
            return

        cls.current_method.run()
