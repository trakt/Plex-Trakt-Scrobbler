from plugin.core.backup.base import BackupManagerBase
from plugin.core.backup.database import DatabaseBackupManager
from plugin.core.backup.policy import BackupPolicyMaintenance
from plugin.core.helpers.thread import spawn

import logging

log = logging.getLogger(__name__)


class BackupManager(BackupManagerBase):
    database = DatabaseBackupManager

    @classmethod
    def maintenance(cls, block=True):
        """Ensures number of backups in each group matches retention policy, runs consolidation
           deletion, and archival tasks if the policy has been exceeded.

        :param block: Block execution until maintenance is complete
        :type block: bool
        """

        if not block:
            return spawn(cls.maintenance, block=True)

        log.debug('Starting backup maintenance...')

        # Run policy maintenance tasks
        policy_maintenance = BackupPolicyMaintenance()
        policy_maintenance.run()
