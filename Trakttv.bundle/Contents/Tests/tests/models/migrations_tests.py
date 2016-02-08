from plugin.models.core import migrations_path

from peewee_migrate.core import Router, Migrator
from playhouse.apsw_ext import APSWDatabase
import logging

log = logging.getLogger(__name__)


def test_schema_specifications():
    # Create database
    db = APSWDatabase(':memory:', autorollback=True, journal_mode='WAL', timeout=3000)

    # Create migration router
    router = Router(migrations_path, DATABASE=db)
    migrator = Migrator(db)

    # Run each migration, and validate the specification
    for name in router.fs_migrations:
        # Execute migration
        router.run_one(name, migrator)

        # Match specification against migration
        assert router.match() == name
