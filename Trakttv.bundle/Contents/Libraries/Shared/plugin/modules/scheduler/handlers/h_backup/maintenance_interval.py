from plugin.core.backup import BackupManager
from plugin.modules.scheduler.handlers.core.base import Handler


class BackupMaintenanceIntervalHandler(Handler):
    key = 'backup.interval'

    def run(self, job):
        # Trigger backup maintenance
        BackupManager.maintenance(block=False)

        return True
