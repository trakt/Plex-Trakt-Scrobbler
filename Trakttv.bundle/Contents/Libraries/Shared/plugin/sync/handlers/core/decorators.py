import logging

log = logging.getLogger(__name__)


def bind(action, modes=None):
    def outer(func):
        func.binding = {
            'action': action,
            'modes': modes
        }

        return func

    return outer
