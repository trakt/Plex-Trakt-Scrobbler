from plugin.core.database.manager import DatabaseManager

import os

migrations_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'migrations'))

# Connect to database
db = DatabaseManager.main()
