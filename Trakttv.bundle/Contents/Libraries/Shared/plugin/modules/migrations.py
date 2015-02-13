from plugin.core.helpers.thread import module
from plugin.models.core import db_path, migrations_path

from peewee_migrate.core import Router
import logging

log = logging.getLogger(__name__)


@module(start=True, priority=0, blocking=True)
class Migrations(object):
    @classmethod
    def start(cls):
        log.debug('db_path: %r', db_path)
        log.debug('migrations_path: %r', migrations_path)

        # Run migrations
        router = Router(migrations_path, DATABASE='sqlite:///%s' % db_path)
        router.run()
