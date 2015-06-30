from plugin.models.core import db, migrations_path
from plugin.modules.migrations.core.base import Migration

from peewee_migrate.core import Router
import logging

log = logging.getLogger(__name__)


class SchemaMigration(Migration):
    def run(self):
        log.debug('migrations_path: %r', migrations_path)

        # Run schema migrations
        router = Router(migrations_path, DATABASE=db)
        router.run()
