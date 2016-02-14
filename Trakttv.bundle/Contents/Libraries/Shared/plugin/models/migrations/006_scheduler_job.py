def migrate(migrator, database):
    migrator.drop_not_null('scheduler.job', 'trigger')
    migrator.drop_not_null('scheduler.job', 'due_at')

#
# Schema specification (for migration verification)
#

SPEC = {
    'scheduler.job': {
        'account_id':               'INTEGER PRIMARY KEY NOT NULL',
        'task_id':                  'VARCHAR(60) PRIMARY KEY NOT NULL',

        'trigger':                  'TEXT',

        'ran_at':                   'DATETIME',
        'due_at':                   'DATETIME'
    }
}
