from plugin.sync.core.enums import SyncMode

import inspect
import logging

log = logging.getLogger(__name__)


class MediaHandler(object):
    media = None

    def __init__(self, data, main):
        self.__parent = data
        self.__main = main

        self.__handlers = {}

    @property
    def parent(self):
        return self.__parent

    def discover(self):
        for key in dir(self):
            if key.startswith('_'):
                continue

            # Retrieve function
            try:
                func = getattr(self, key)
            except Exception:
                continue

            if not func or not inspect.ismethod(func):
                continue

            # Retrieve binding metadata
            binding = getattr(func, 'binding', None)

            if not binding:
                continue

            # Parse metadata, set defaults
            action = binding['action']

            modes = binding['modes'] or [
                SyncMode.FastPull,

                SyncMode.Pull,
                SyncMode.Push,

                SyncMode.Full
            ]

            if not action or not modes:
                continue

            # Store callback in `__handlers`
            for mode in modes:
                if mode not in self.__handlers:
                    self.__handlers[mode] = {}

                self.__handlers[mode][action] = func

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
        func = self.__handlers.get(self.current.mode, {}).get(action)

        if func is None:
            log.debug('Unable to find handler for mode %r, action %r', self.current.mode, action)
            return False

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
