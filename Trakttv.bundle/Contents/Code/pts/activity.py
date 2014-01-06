from core.logger import Logger
from core.method_manager import Method, Manager

log = Logger('pts.activity')


class ActivityMethod(Method):
    def get_name(self):
        return 'Activity_%s' % self.name


class Activity(Manager):
    tag = 'pts.activity'

    available = []
    enabled = []
