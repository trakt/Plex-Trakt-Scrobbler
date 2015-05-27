from plugin.sync.core.enums import SyncMode

import logging

log = logging.getLogger(__name__)


class DataHandler(object):
    data = None
    children = None

    def __init__(self, main):
        self.__main = main
        self.__children = dict(self.__construct_children(main))

    @property
    def current(self):
        return self.__main.current

    @property
    def handlers(self):
        return self.__main.handlers

    def __construct_children(self, main):
        if self.children is None:
            return

        for cls in self.children:
            if cls.media is None:
                log.warn('%r does not has a valid "media" attribute', cls)
                continue

            yield cls.media, cls(self, main)

    def run(self, media, mode, *args, **kwargs):
        module = self.__children.get(media)

        if module is None:
            log.warn('No handler found for media: %r', media)
            return

        module.run(mode, *args, **kwargs)


class MediaHandler(object):
    media = None

    def __init__(self, data, main):
        self.__data = data
        self.__main = main

    @property
    def current(self):
        return self.__main.current

    @property
    def handlers(self):
        return self.__main.handlers

    @staticmethod
    def build_action(*args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def get_operands(p_settings, t_item):
        raise NotImplementedError

    def run(self, mode, *args, **kwargs):
        if mode == SyncMode.FastPull:
            return self.fast_pull(*args, **kwargs)

        if mode == SyncMode.Full:
            return self.full(*args, **kwargs)

        if mode == SyncMode.Pull:
            return self.pull(*args, **kwargs)

        if mode == SyncMode.Push:
            return self.push(*args, **kwargs)

        log.warn('No handler found for action: %r', mode)

    def fast_pull(self, *args, **kwargs):
        raise NotImplementedError

    def full(self, *args, **kwargs):
        raise NotImplementedError

    def pull(self, *args, **kwargs):
        raise NotImplementedError

    def push(self, *args, **kwargs):
        raise NotImplementedError

    #
    # Action handlers
    #

    def execute_actions(self, changes, key, p_settings):
        for action, t_items in changes.items():
            if key not in t_items:
                continue

            self.execute_action(action, key, p_settings, t_items[key])

    def execute_action(self, action, args):
        # Find matching function
        func = getattr(self, 'on_%s' % action, None)

        if func is None:
            raise NotImplementedError

        # Execute action
        parameters = self.build_action(*args)

        if parameters is None:
            return False

        return func(**parameters)

    def get_action(self, p_value, t_value):
        if p_value is None and t_value is not None:
            return 'added'

        if p_value is not None and t_value is None:
            return 'removed'

        if p_value != t_value:
            return 'changed'

        return None

    def on_added(self, *args, **kwargs):
        raise NotImplementedError

    def on_removed(self, *args, **kwargs):
        raise NotImplementedError

    def on_changed(self, *args, **kwargs):
        raise NotImplementedError
