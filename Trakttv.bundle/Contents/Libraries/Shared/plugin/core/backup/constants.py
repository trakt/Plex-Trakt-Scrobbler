from plugin.core.environment import Environment
import os


BACKUP_PATH = os.path.join(Environment.path.plugin_data, 'Backups')

BACKUP_RETENTION = [
    {'period':   'day', 'count':   4, 'format': 'raw'},
    {'period':  'week', 'count':   7, 'format': 'raw'},
    {'period': 'month', 'count':  21, 'format': 'archive'},
    {'period':  'year', 'count': 210, 'format': 'archive'},
]