# -*- coding: utf-8 -*-
'''
HDF5 database store.

shove's URI for HDF5 stores follows the form:

hdf5://<path>/<group>

Where <path> is a URL path to a HDF5 database. Alternatively, the native
pathname to a HDF5 database can be passed as the 'engine' parameter.
<group> is the name of the database.
'''

try:
    import h5py
except ImportError:
    raise ImportError('requires h5py library')

from shove.store import ClientStore

__all__ = ['HDF5Store']


class HDF5Store(ClientStore):

    '''HDF5-based object storage frontend.'''

    init = 'hdf5://'

    def __init__(self, engine, **kw):
        super(HDF5Store, self).__init__(engine, **kw)
        engine, group = self._engine.rsplit('/')
        self._store = h5py.File(engine).require_group(group).attrs
