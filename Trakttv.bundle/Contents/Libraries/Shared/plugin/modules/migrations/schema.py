from plugin.core.database.manager import DatabaseManager
from plugin.models.core import db, migrations_path
from plugin.modules.migrations.core.base import Migration

import logging

log = logging.getLogger(__name__)

# Try import "peewee_migrate" router
try:
    from peewee_migrate.core import Router
except (ImportError, NameError):
    Router = None


class SchemaMigration(Migration):
    def run(self):
        log.debug('migrations_path: %r', migrations_path)

        # Build migration router
        router = self._build_router()

        if not router:
            return False

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

        # Build migration router
        router = cls._build_router()

        if not router:
            return False

        # Run migrations
        router.run()

        # Log message to channel menu
        from plugin.managers.message import MessageManager
        from plugin.models import Message

        MessageManager.get.from_message(logging.WARNING,
            message="Plugin database has been reset due to schema corruption",
            description="Your corrupted database is available at: "
                        "\"Plug-in Support\\Data\\com.plexapp.plugins.trakttv\\Backups\\main.bgr\"",
            code=Message.Code.DatabaseSchemaCorruptionReset
        )

        return True

    @staticmethod
    def _build_router():
        if not Router:
            return None

        return Router(migrations_path, DATABASE=db)
