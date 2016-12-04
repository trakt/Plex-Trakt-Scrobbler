def migrate(migrator, database):
    # Message
    migrator.drop_index('message', 'message_exception_hash')
    migrator.add_index('message', ('type', 'exception_hash'), True)

#
# Schema specification (for migration verification)
#

SPEC = {}
