from oem.core.exceptions import AbsoluteNumberRequiredError  # NOQA

import logging

log = logging.getLogger(__name__)


try:
    from oem.client import Client
    OemClient = Client
except ImportError as ex:
    log.warn('Unable to import client - %s', ex, exc_info=True)
    Client = None
    OemClient = None
