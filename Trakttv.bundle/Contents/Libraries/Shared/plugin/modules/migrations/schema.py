from plugin.core.database.manager import DatabaseManager
from plugin.models.core import db, migrations_path
from plugin.modules.migrations.core.base import Migration

from peewee_migrate.core import Router
import logging

log = logging.getLogger(__name__)


class SchemaMigration(Migration):
    def run(self):
        log.debug('migrations_path: %r', migrations_path)

        router = self._build_router()

        # Validate current schema
        if not router.validate():
            log.error('Detected corrupt/invalid database schema, resetting database...')
            return self.reset()
        else:
            log.info('Database schema is valid')

        # Run schema migrations
        router.run()
        return True

    @classmethod
    def reset(cls):
        if not DatabaseManager.reset('main', db, 'invalid-schema'):
            # Unable to reset database
            return False

        # Run migrations
        router = cls._build_router()
        router.run()

        # Log message to channel menu
        from plugin.managers.message import MessageManager
        from plugin.models import Message

        MessageManager.get.from_message(logging.WARNING,
            "Plugin database has been automatically reset due to schema corruption, see http://bit.ly/TFPx90101 for more details",
            code=Message.Code.DatabaseSchemaCorruptionReset
        )

        return True

    @staticmethod
    def _build_router():
        return Router(migrations_path, DATABASE=db)
