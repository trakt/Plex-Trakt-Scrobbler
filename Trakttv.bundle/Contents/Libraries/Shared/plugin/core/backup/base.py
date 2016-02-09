from plugin.core.backup.constants import BACKUP_PATH
from plugin.core.helpers.variable import json_date_serializer

import json
import logging
import os

log = logging.getLogger(__name__)


class BackupManagerBase(object):
    @staticmethod
    def path(group, timestamp, tag=None):
        # Build directory
        directory = os.path.join(
            BACKUP_PATH,
            group,
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

        return directory, os.path.join(directory, name)

    @staticmethod
    def write_metadata(path, **metadata):
        log.debug('Writing backup metadata to %r', path)

        with open(path, 'wb') as fp:
            json.dump(metadata, fp, default=json_date_serializer)
