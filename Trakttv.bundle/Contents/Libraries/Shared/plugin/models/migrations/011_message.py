def migrate(migrator, database):
    # Message
    migrator.add_index('message', ('code', ), True)

#
# Schema specification (for migration verification)
#

SPEC = {}
