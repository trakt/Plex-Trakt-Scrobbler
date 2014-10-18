# -*- coding: utf-8 -*-
'''
Durus object database frontend.

shove's URI for Durus stores follows the form:

durus://<path>

Where the path is a URI path to a Durus FileStorage database. Alternatively, a
native pathname to a Durus database can be passed as the 'engine' parameter.
'''

try:
    from durus.connection import Connection
    from durus.file_storage import FileStorage
except ImportError:
    raise ImportError('requires Durus library')

from shove.store import SyncStore

__all__ = ['DurusStore']


class DurusStore(SyncStore):

    '''Durus-based object storage frontend.'''

    init = 'durus://'

    def __init__(self, engine, **kw):
        super(DurusStore, self).__init__(engine, **kw)
        self._db = FileStorage(self._engine)
        self._connection = Connection(self._db)
        self.sync = self._connection.commit
        self._store = self._connection.get_root()

    def close(self):
        '''Closes all open storage and connections.'''
        self.sync()
        super(DurusStore, self).close()
        self._db.close()
