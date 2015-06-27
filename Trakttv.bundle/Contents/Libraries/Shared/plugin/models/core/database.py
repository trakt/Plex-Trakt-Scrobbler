from plugin.core.database import Database

import os

migrations_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'migrations'))

# Connect to database
db = Database.main()
