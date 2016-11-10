from plugin.core.backup.sources.base import BackupSource
from plugin.core.backup.models import BackupRevision
from plugin.core.database.connection import db_connect, db_connection

from datetime import datetime
import logging
import os

log = logging.getLogger(__name__)


class DatabaseBackupSource(BackupSource):
    @classmethod
    def backup(cls, group, database, tag=None, metadata=None):
        timestamp = datetime.now()

        # Build backup directory/name
        directory, name, path = cls.path(group, timestamp, tag)
        destination_path = path + '.db'

        # Ensure directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)

        log.info('[%s] Backing up database to %r', group, destination_path)

        # Backup database
        destination = db_connect(destination_path, 'raw', name='backup database')

        # Get `database` connection
        source = db_connection(database)

        # Copy `source` database to `destination`
        try:
            cls._copy(group, source, destination)
        finally:
            # Close `destination` database
            destination.close()

        # Ensure path exists
        if not os.path.exists(destination_path):
            log.error('Backup failed (file doesn\'t exist)')
            return False

        # Construct revision
        revision = BackupRevision(
            timestamp, [
                name + '.db'
            ],

            tag=tag,
            attributes=metadata or {}
        )

        # Write backup metadata
        revision.save(path + '.bre')

        return True

    @classmethod
    def _copy(cls, group, source, destination):
        with destination.backup('main', source, 'main') as b:
            # Run until backup is completed
            while not b.done:
                b.step(100)

                # Report progress
                progress = float(b.pagecount - b.remaining) / b.pagecount

                log.debug('[%s] Backup Progress: %3d%%', group, progress * 100)
