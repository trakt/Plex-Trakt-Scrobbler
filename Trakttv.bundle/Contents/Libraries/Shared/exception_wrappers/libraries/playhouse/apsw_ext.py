from __future__ import absolute_import

from exception_wrappers.exceptions import ModuleDisabledError
from exception_wrappers.manager import ExceptionSource, ExceptionWrapper
import sys


exw_enabled = False

exw_exception = None
exw_exc_info = (None, None, None)

# Try import "peewee", generate skeleton if an error is raised
try:
    from peewee import *
    from peewee import Database
except ImportError as ex:
    # Generate skeleton database class
    class Database(object):
        commit_select = False

# Try import "playhouse.apsw_ext", generate skeleton if an error is raised
try:
    from playhouse.apsw_ext import *
    exw_enabled = True
except ImportError as ex:
    # Emit event
    ExceptionWrapper.add(ExceptionSource.Peewee, sys.exc_info(), 'playhouse.apsw_ext')

    # Update module state
    exw_exception = ex
    exw_exc_info = sys.exc_info()

    # Generate skeleton cursor class
    class Cursor(object):
        lastrowid = 0
        rowcount = 0

        def execute(self, *args, **kwargs):
            raise ModuleDisabledError(exw_exception)

        def fetchone(self, *args, **kwargs):
            raise ModuleDisabledError(exw_exception)

        def close(self, *args, **kwargs):
            raise ModuleDisabledError(exw_exception)

    # Generate skeleton connection class
    class Connection(object):
        def cursor(self, *args, **kwargs):
            return Cursor()

        def commit(self, *args, **kwargs):
            raise ModuleDisabledError(exw_exception)

        def rollback(self, *args, **kwargs):
            raise ModuleDisabledError(exw_exception)

    # Generate skeleton database class
    class APSWDatabase(Database):
        def __init__(self, *args, **kwargs):
            super(APSWDatabase, self).__init__(*args, **kwargs)

        def _connect(self, *args, **kwargs):
            return Connection()
