from plugin.core.helpers.variable import merge
from plugin.managers.core.base import Manager
from plugin.models import db, Account

from plex import Plex
import logging

log = logging.getLogger(__name__)


class AccountManager(Manager):
    model = Account
