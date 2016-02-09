from plugin.core.environment import Environment
import os
import re


BACKUP_PATH = os.path.join(Environment.path.plugin_data, 'Backups')

BACKUP_RETENTION = {
    'year':  {'count':   6, 'action': 'archive'},
    'month': {'count':  28, 'action': 'archive'},
    'week':  {'count':  14},
    'day':   {'count':   4}
}

BACKUP_NAME_REGEX = re.compile('^(?P<day>\d+)_(?P<time>\d+)(_(?P<tag>\w+))?\.bme$')
