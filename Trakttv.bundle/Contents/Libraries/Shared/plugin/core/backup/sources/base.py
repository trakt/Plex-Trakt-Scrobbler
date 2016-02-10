from plugin.core.backup.constants import BACKUP_PATH

import logging
import os

log = logging.getLogger(__name__)


class BackupSource(object):
    @staticmethod
    def path(group, timestamp, tag=None):
        # Build directory
        directory = os.path.join(
            BACKUP_PATH,
            group + '.bgr',
            str(timestamp.year),
            '%02d' % timestamp.month
        )

        # Build name
        name = '%02d_%02d%02d%02d%s' % (
            timestamp.day,
            timestamp.hour,
            timestamp.minute,
            timestamp.second,
            ('_%s' % tag) if tag else ''
        )

        return directory, name, os.path.join(directory, name)
