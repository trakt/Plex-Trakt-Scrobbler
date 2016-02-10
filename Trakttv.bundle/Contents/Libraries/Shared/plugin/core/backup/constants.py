from plugin.core.environment import Environment
import os
import re

# Backup directory/file types
#  - *.bar (Backup Archive)
#  - *.bgr (Backup Group)
#  - *.bre (Backup Revision)

BACKUP_PATH = os.path.join(Environment.path.plugin_data, 'Backups')

BACKUP_PERIODS = [
    'day',
    'week',
    'month',
    'year'
]

BACKUP_RETENTION = {
    'year': {
        'files': '*.bar',

        # Compress monthly archives
        'archive': True
    },
    'month': {
        'files': '*.bre',

        'compact': {
            'maximum': 28
        },

        # Compress backup revisions
        'archive': True
    },
    'week': {
        'files': '*.bre',

        'compact': {
            'maximum': 14
        }
    },
    'day': {
        'files': '*.bre',

        'compact': {
            'maximum': 4
        }
    }
}

BACKUP_NAME_REGEX = re.compile('^\d{2}(?:_\d{6}(?:_\w+)?)?\.(?:bar|bre)$')
