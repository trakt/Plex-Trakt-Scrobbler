from plugin.core.backup.base import BackupManagerBase
from plugin.core.helpers.database import db_connect, db_connection

from datetime import datetime
import logging
import os

log = logging.getLogger(__name__)


class DatabaseBackupManager(BackupManagerBase):
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
        destination = db_connect(destination_path, 'raw')

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

        # Write backup metadata
        cls.write_metadata(
            path + '.bme',
            timestamp=timestamp,
            tag=tag,
            **(metadata or {})
        )

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
