import logging

from plugin.managers.core.base import Manager
from plugin.models import Account


log = logging.getLogger(__name__)


class AccountManager(Manager):
    model = Account
