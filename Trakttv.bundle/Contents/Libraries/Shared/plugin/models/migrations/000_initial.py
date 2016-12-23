from plugin.models.core import db

from exception_wrappers.libraries.playhouse.apsw_ext import *


def migrate(migrator, database):
    migrator.create_tables(
        #
        # Plex
        #
        PlexAccount,

        PlexBasicCredential,

        #
        # Sync
        #
        SyncStatus,

        SyncResult,
        SyncResultError,
        SyncResultException,

        #
        # Trakt
        #
        TraktAccount,

        TraktBasicCredential,
        TraktOAuthCredential,

        #
        # Main
        #
        Account,
        Exception,
        Message,
        Session,

        ConfigurationOption,

        ActionHistory,
        ActionQueue,

        Client,
        ClientRule,

        User,
        UserRule
    )


class Account(Model):
    class Meta:
        database = db

    name = CharField(null=True, unique=True)
    thumb = TextField(null=True)


class Client(Model):
    class Meta:
        database = db
        db_table = 'session.client'

    account = ForeignKeyField(Account, 'clients', null=True)

    # Identification
    key = CharField(unique=True)
    name = CharField(null=True)

    # Device
    device_class = CharField(null=True)
    platform = CharField(null=True)
    product = CharField(null=True)
    version = CharField(null=True)

    # Network
    host = CharField(null=True)
    address = CharField(null=True)
    port = IntegerField(null=True)

    # Protocol
    protocol = CharField(null=True)
    protocol_capabilities = CharField(null=True)
    protocol_version = CharField(null=True)


class ClientRule(Model):
    class Meta:
        database = db
        db_table = 'session.client.rule'

    account = ForeignKeyField(Account, 'client_rules')

    key = CharField(null=True)
    name = CharField(null=True)
    address = CharField(null=True)

    priority = IntegerField()


class User(Model):
    class Meta:
        database = db
        db_table = 'session.user'

    account = ForeignKeyField(Account, 'users', null=True)

    # Identification
    key = IntegerField(unique=True)
    name = CharField(null=True)

    thumb = CharField(null=True)


class UserRule(Model):
    class Meta:
        database = db
        db_table = 'session.user.rule'

    account = ForeignKeyField(Account, 'user_rules')

    name = CharField(null=True)

    priority = IntegerField()


class Session(Model):
    class Meta:
        database = db

    account = ForeignKeyField(Account, 'sessions', null=True)
    client = ForeignKeyField(Client, 'sessions', to_field='key', null=True)
    user = ForeignKeyField(User, 'sessions', to_field='key', null=True)

    rating_key = IntegerField(null=True)
    session_key = TextField(null=True, unique=True)

    state = CharField(null=True)

    progress = FloatField(null=True)

    duration = IntegerField(null=True)
    view_offset = IntegerField(null=True)


class ConfigurationOption(Model):
    class Meta:
        database = db
        db_table = 'configuration.option'

        primary_key = CompositeKey('account', 'key')

    account = ForeignKeyField(Account, 'sync_configuration')

    key = CharField(max_length=60)
    value = BlobField()

#
# Action
#

class ActionHistory(Model):
    class Meta:
        database = db
        db_table = 'action.history'

    account = ForeignKeyField(Account, 'action_history')
    session = ForeignKeyField(Session, 'action_history', null=True)

    event = CharField()
    performed = CharField(null=True)

    queued_at = DateTimeField()
    sent_at = DateTimeField()


class ActionQueue(Model):
    class Meta:
        database = db
        db_table = 'action.queue'
        primary_key = CompositeKey('session', 'event')

    account = ForeignKeyField(Account, 'action_queue')
    session = ForeignKeyField(Session, 'action_queue', null=True)

    event = CharField()
    request = BlobField()

    queued_at = DateTimeField()

#
# Exception / Message
#

class Message(Model):
    class Meta:
        database = db
        db_table = 'message'

    code = IntegerField(null=True)
    type = IntegerField()

    last_logged_at = DateTimeField()
    last_viewed_at = DateTimeField(null=True)

    # Tracking data
    exception_hash = CharField(null=True, unique=True, max_length=32)
    revision = IntegerField(null=True)

    version_base = CharField(max_length=12)
    version_branch = CharField(max_length=42)

    # User-friendly explanation
    summary = CharField(null=True, max_length=160)  # Short single-line summary
    description = TextField(null=True)  # Extra related details


class Exception(Model):
    class Meta:
        database = db
        db_table = 'exception'

    error = ForeignKeyField(Message, 'exceptions', null=True)

    type = TextField()
    message = TextField()
    traceback = TextField()

    hash = CharField(null=True, max_length=32)

    timestamp = DateTimeField()
    version_base = CharField(max_length=12)
    version_branch = CharField(max_length=42)

#
# Plex
#

class PlexAccount(Model):
    class Meta:
        database = db
        db_table = 'plex.account'

    account = ForeignKeyField(Account, 'plex_accounts', unique=True)

    username = CharField(null=True, unique=True)
    thumb = TextField(null=True)


class PlexBasicCredential(Model):
    class Meta:
        database = db
        db_table = 'plex.credential.basic'

    account = ForeignKeyField(PlexAccount, 'basic_credentials', unique=True)

    password = CharField(null=True)

    # Authorization
    token = CharField(null=True)

#
# Trakt
#

class TraktAccount(Model):
    class Meta:
        database = db
        db_table = 'trakt.account'

    account = ForeignKeyField(Account, 'trakt_accounts', unique=True)

    username = CharField(null=True, unique=True)
    thumb = TextField(null=True)

    cover = TextField(null=True)
    timezone = TextField(null=True)

    refreshed_at = DateTimeField(null=True)


class TraktBasicCredential(Model):
    class Meta:
        database = db
        db_table = 'trakt.credential.basic'

    account = ForeignKeyField(TraktAccount, 'basic_credentials', unique=True)

    password = CharField(null=True)

    # Authorization
    token = CharField(null=True)


class TraktOAuthCredential(Model):
    class Meta:
        database = db
        db_table = 'trakt.credential.oauth'

    account = ForeignKeyField(TraktAccount, 'oauth_credentials', unique=True)

    code = CharField(null=True)

    # Authorization
    access_token = CharField(null=True)
    refresh_token = CharField(null=True)

    created_at = IntegerField(null=True)
    expires_in = IntegerField(null=True)

    token_type = CharField(null=True)
    scope = CharField(null=True)

#
# Sync
#

class SyncStatus(Model):
    class Meta:
        database = db
        db_table = 'sync.status'

    account = ForeignKeyField(Account, 'sync_status')

    mode = IntegerField()
    section = CharField(null=True, max_length=3)


class SyncResult(Model):
    class Meta:
        database = db
        db_table = 'sync.result'

    status = ForeignKeyField(SyncStatus, 'history')

    # Timestamps
    started_at = DateTimeField(null=True)
    ended_at = DateTimeField(null=True)

    # Result
    success = BooleanField(null=True)


class SyncResultError(Model):
    class Meta:
        database = db
        db_table = 'sync.result.error'

    result = ForeignKeyField(SyncResult, 'errors')
    error = ForeignKeyField(Message, 'results')


class SyncResultException(Model):
    class Meta:
        database = db
        db_table = 'sync.result.exception'

    result = ForeignKeyField(SyncResult, 'exceptions')
    exception = ForeignKeyField(Exception, 'results')

#
# Schema specification (for migration verification)
#

SPEC = {
    #
    # Account
    #

    'account': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',

        'name':                     'VARCHAR(255)',
        'thumb':                    'TEXT'
    },
    'plex.account': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'username':                 'VARCHAR(255)',
        'thumb':                    'TEXT'
    },
    'plex.credential.basic': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'password':                 'VARCHAR(255)',

        'token':                    'VARCHAR(255)'
    },

    'trakt.account': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'username':                 'VARCHAR(255)',
        'thumb':                    'TEXT',

        'cover':                    'TEXT',
        'timezone':                 'TEXT',

        'refreshed_at':             'DATETIME'
    },
    'trakt.credential.basic': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'password':                 'VARCHAR(255)',

        'token':                    'VARCHAR(255)'
    },
    'trakt.credential.oauth': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'code':                     'VARCHAR(255)',

        'access_token':             'VARCHAR(255)',
        'refresh_token':            'VARCHAR(255)',

        'created_at':               'INTEGER',
        'expires_in':               'INTEGER',

        'token_type':               'VARCHAR(255)',
        'scope':                    'VARCHAR(255)'
    },

    #
    # Session
    #

    'session': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER',
        'client_id':                'VARCHAR(255)',
        'user_id':                  'INTEGER',

        'rating_key':               'INTEGER',
        'session_key':              'TEXT',

        'state':                    'VARCHAR(255)',

        'progress':                 'REAL',

        'duration':                 'INTEGER',
        'view_offset':              'INTEGER'
    },

    'session.client': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER',

        'key':                      'VARCHAR(255) NOT NULL',
        'name':                     'VARCHAR(255)',

        'device_class':             'VARCHAR(255)',
        'platform':                 'VARCHAR(255)',
        'product':                  'VARCHAR(255)',
        'version':                  'VARCHAR(255)',

        'host':                     'VARCHAR(255)',
        'address':                  'VARCHAR(255)',
        'port':                     'INTEGER',

        'protocol':                 'VARCHAR(255)',
        'protocol_capabilities':    'VARCHAR(255)',
        'protocol_version':         'VARCHAR(255)'
    },
    'session.client.rule': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'key':                      'VARCHAR(255)',
        'name':                     'VARCHAR(255)',
        'address':                  'VARCHAR(255)',

        'priority':                 'INTEGER NOT NULL'
    },

    'session.user': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER',

        'key':                      'INTEGER NOT NULL',
        'name':                     'VARCHAR(255)',

        'thumb':                    'VARCHAR(255)',
    },
    'session.user.rule': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'name':                     'VARCHAR(255)',

        'priority':                 'INTEGER NOT NULL'
    },

    #
    # Configuration
    #

    'configuration.option': {
        'key':                      'VARCHAR(60) PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER PRIMARY KEY NOT NULL',

        'value':                    'BLOB NOT NULL'
    },

    #
    # Actions
    #

    'action.history': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',
        'session_id':               'INTEGER',

        'event':                    'VARCHAR(255) NOT NULL',
        'performed':                'VARCHAR(255)',

        'queued_at':                'DATETIME NOT NULL',
        'sent_at':                  'DATETIME NOT NULL'
    },
    'action.queue': {
        'account_id':               'INTEGER NOT NULL',
        'session_id':               'INTEGER PRIMARY KEY',

        'event':                    'VARCHAR(255) PRIMARY KEY NOT NULL',
        'request':                  'BLOB NOT NULL',

        'queued_at':                'DATETIME NOT NULL',
    },

    #
    # Messages/Exceptions
    #

    'message': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',

        'code':                     'INTEGER',
        'type':                     'INTEGER NOT NULL',

        'last_logged_at':           'DATETIME NOT NULL',
        'last_viewed_at':           'DATETIME',

        'exception_hash':           'VARCHAR(32)',
        'revision':                 'INTEGER',

        'version_base':             'VARCHAR(12) NOT NULL',
        'version_branch':           'VARCHAR(42) NOT NULL',

        'summary':                  'VARCHAR(160)',
        'description':              'TEXT'
    },
    'exception': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'error_id':                 'INTEGER',

        'type':                     'TEXT NOT NULL',
        'message':                  'TEXT NOT NULL',
        'traceback':                'TEXT NOT NULL',

        'hash':                     'VARCHAR(32)',

        'timestamp':                'DATETIME NOT NULL',
        'version_base':             'VARCHAR(12) NOT NULL',
        'version_branch':           'VARCHAR(42) NOT NULL',
    },

    #
    # Syncing
    #

    'sync.status': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'account_id':               'INTEGER NOT NULL',

        'mode':                     'INTEGER NOT NULL',
        'section':                  'VARCHAR(3)'
    },

    'sync.result': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'status_id':                'INTEGER NOT NULL',

        'started_at':               'DATETIME',
        'ended_at':                 'DATETIME',

        'success':                  'SMALLINT'
    },
    'sync.result.error': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'result_id':                'INTEGER NOT NULL',
        'error_id':                 'INTEGER NOT NULL'
    },
    'sync.result.exception': {
        'id':                       'INTEGER PRIMARY KEY NOT NULL',
        'result_id':                'INTEGER NOT NULL',
        'exception_id':             'INTEGER NOT NULL'
    },
}
