import logging

log = logging.getLogger(__name__)


class DataHandler(object):
    data = None
    mode = None

    children = None

    def __init__(self, task):
        self.__task = task
        self.__children = dict(self.__construct_children(task))

    @property
    def current(self):
        return self.__task

    @property
    def handlers(self):
        return self.__task.handlers

    def __construct_children(self, task):
        if self.children is None:
            return

        for cls in self.children:
            if cls.media is None:
                log.warn('%r does not has a valid "media" attribute', cls)
                continue

            obj = cls(self, task)
            obj.discover()

            yield cls.media, obj

    def run(self, media, mode, *args, **kwargs):
        module = self.__children.get(media)

        if module is None:
            log.warn('No handler found for media: %r', media)
            return

        module.run(mode, *args, **kwargs)
