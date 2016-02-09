from plugin.core.backup.base import BackupManagerBase
from plugin.core.backup.database import DatabaseBackupManager

import logging

log = logging.getLogger(__name__)


class BackupManager(BackupManagerBase):
    database = DatabaseBackupManager

    @classmethod
    def maintenance(cls):
        """Ensures number of backups in each group matches retention policy, runs consolidation
           deletion, and archival tasks if the policy has been exceeded.
        """
        pass
