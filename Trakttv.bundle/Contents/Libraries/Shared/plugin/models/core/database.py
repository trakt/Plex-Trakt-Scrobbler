from plugin.core.environment import Environment

from peewee import SqliteDatabase
import logging
import os

log = logging.getLogger(__name__)

db_path = os.path.join(Environment.path.plugin_data, 'plugin.db')
migrations_path = os.path.join(os.path.dirname(__file__), '..', 'migrations')

# Connect to database
db = SqliteDatabase(db_path, threadlocals=True)
