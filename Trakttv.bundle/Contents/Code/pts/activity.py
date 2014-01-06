from core.eventing import EventHandler
from core.logger import Logger
from core.method_manager import Method, Manager

log = Logger('pts.activity')


class ActivityMethod(Method):
    on_update_collection = EventHandler()

    def __init__(self, now_playing):
        super(ActivityMethod, self).__init__()

        self.now_playing = now_playing

    def get_name(self):
        return 'Activity_%s' % self.name

    def update_collection(self, item_id, action):
        self.now_playing.update_collection(item_id, action)


class Activity(Manager):
    on_update_collection = EventHandler()

    @classmethod
    def update_collection(cls, item_id, action):
        cls.on_update_collection.fire(item_id, action)
