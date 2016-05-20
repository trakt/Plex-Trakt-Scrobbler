from plugin.sync.core.enums import SyncMode

import inspect
import logging

log = logging.getLogger(__name__)


class MediaHandler(object):
    media = None

    def __init__(self, data, task):
        self.__parent = data
        self.__task = task

        self.__handlers = {}

    @property
    def configuration(self):
        return self.__task.configuration

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
        return self.__task

    @property
    def handlers(self):
        return self.__task.handlers

    @staticmethod
    def build_action(*args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def get_operands(p_item, t_item):
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

            self.execute_action(
                action,
                key=key,
                p_settings=p_settings,
                t_item=t_items[key]
            )

    def execute_action(self, action, **kwargs):
        # Find matching function
        func = self.__handlers.get(self.current.mode, {}).get(action)

        if func is None:
            #log.debug('Unable to find handler for mode %r, action %r', self.current.mode, action)
            return False

        # Execute action
        parameters = self.build_action(
            action=action,
            **kwargs
        )

        if parameters is None:
            return False

        return func(**parameters)

    def get_action(self, p_value, t_value):
        raise NotImplementedError

    def on_added(self, *args, **kwargs):
        raise NotImplementedError

    def on_removed(self, *args, **kwargs):
        raise NotImplementedError

    def on_changed(self, *args, **kwargs):
        raise NotImplementedError

    #
    # Artifacts
    #

    def store_show(self, action, guid, p_key=None, p_show=None, **kwargs):
        return self.current.artifacts.store_show(
            self.parent.data, action, guid,
            p_key=p_key,
            p_show=p_show,
            **kwargs
        )

    def store_episode(self, action, guid, identifier, p_key=None, p_show=None, p_episode=None, **kwargs):
        return self.current.artifacts.store_episode(
            self.parent.data, action, guid, identifier,
            p_key=p_key,
            p_show=p_show,
            p_episode=p_episode,
            **kwargs
        )

    def store_movie(self, action, guid, p_key=None, p_movie=None, **kwargs):
        return self.current.artifacts.store_movie(
            self.parent.data, action, guid,
            p_key=p_key,
            p_movie=p_movie,
            **kwargs
        )
