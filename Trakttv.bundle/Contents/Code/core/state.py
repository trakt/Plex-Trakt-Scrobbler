from core.helpers import error_view, message_view

import functools


class State(object):
    class Types(object):
        initializing    = 10
        configuring     = 20
        starting        = 30

        started         = 40
        error           = 90

    current = Types.initializing
    exception = None

    @classmethod
    def get(cls):
        return cls.current

    @classmethod
    def set(cls, state, exception=None):
        if state < cls.current:
            raise ValueError('Unable to reverse states')

        cls.current = state
        cls.exception = exception

    @classmethod
    def wait(cls, state=Types.started, message='Plugin is starting up...'):
        def wrapper(func):
            @functools.wraps(func)
            def inner(*args, **kwargs):
                if cls.current == State.Types.error:
                    if cls.exception:
                        return error_view(type(cls.exception).__name__, cls.exception.message)

                    return message_view(message='Unknown startup error')

                if cls.current < state:
                    return message_view(message=message)

                return func(*args, **kwargs)

            return inner

        return wrapper
