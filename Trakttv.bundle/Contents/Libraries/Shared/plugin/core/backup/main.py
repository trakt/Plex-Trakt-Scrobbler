from plugin.core.backup.maintenance import BackupMaintenanceManager
from plugin.core.backup.sources import DatabaseBackupSource
from plugin.core.helpers.thread import spawn

from threading import Lock
import logging

log = logging.getLogger(__name__)


class BackupManager(object):
    database = DatabaseBackupSource

    maintenance_lock = Lock()

    @classmethod
    def maintenance(cls, block=True):
        """Ensures number of backups in each group matches retention policy, runs consolidation
           deletion, and archival tasks if the policy has been exceeded.

        :param block: Block execution until maintenance is complete
        :type block: bool
        """

        if not block:
            return spawn(cls.maintenance, block=True)

        if not cls.maintenance_lock.acquire(False):
            log.debug('Backup maintenance already running')
            return

        log.info('Starting backup maintenance...')

        try:
            # Run policy maintenance tasks
            maintenance = BackupMaintenanceManager()
            maintenance.run()
        except Exception as ex:
            log.error('Exception raised during backup maintenance: %s', ex, exc_info=True)
        finally:
            cls.maintenance_lock.release()

        log.info('Backup maintenance complete')
