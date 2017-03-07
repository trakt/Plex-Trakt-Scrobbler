from oem.core.exceptions import AbsoluteNumberRequiredError  # NOQA

import logging

log = logging.getLogger(__name__)


# Set default logging handler to avoid "No handler found" warnings.
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())


# Try import client
try:
    from oem.client import Client
    OemClient = Client
except ImportError as ex:
    log.warn('Unable to import client - %s', ex, exc_info=True)
    Client = None
    OemClient = None
