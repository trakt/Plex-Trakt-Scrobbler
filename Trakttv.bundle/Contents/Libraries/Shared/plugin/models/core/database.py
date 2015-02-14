from plugin.core.environment import Environment

from playhouse.apsw_ext import APSWDatabase
import logging
import os

log = logging.getLogger(__name__)

db_path = os.path.abspath(Environment.path.plugin_database)
migrations_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'migrations'))

# Connect to database
db = APSWDatabase(db_path, journal_mode='WAL')
