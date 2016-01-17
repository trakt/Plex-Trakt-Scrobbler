import logging

log = logging.getLogger(__name__)


class ModeHandler(object):
    data = None
    children = None

    def __init__(self, task):
        self.__task = task
        self.__children = dict(self.__construct_children(task))

    def __construct_children(self, task):
        if self.children is None:
            return

        for cls in self.children:
            if cls.mode is None:
                log.warn('%r does not has a valid "mode" attribute', cls)
                continue

            # `cls.mode` can be defined as a single mode, or list of modes
            if type(cls.mode) is list:
                modes = cls.mode
            else:
                modes = [cls.mode]

            # Construct child module
            obj = cls(task)

            for mode in modes:
                yield mode, obj

    def run(self, media, mode, *args, **kwargs):
        module = self.__children.get(mode)

        if module is None:
            log.warn('No handler found for mode: %r', mode)
            return

        module.run(media, mode, *args, **kwargs)
