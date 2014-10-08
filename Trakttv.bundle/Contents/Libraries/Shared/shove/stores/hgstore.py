# -*- coding: utf-8 -*-
'''
Mercurial versioned object store.

shove's URI for Mercurial-based stores follows the form:

hg://<path>

Where the path is a URI path to a Mercurial repository on a local filesystem.
Alternatively, a native pathname to the repository can be passed as the
'engine' argument.
'''

try:
    import hgapi
except ImportError:
    raise ImportError('requires hgapi library')

from shove.store import FileStore


class HgStore(FileStore):

    '''Mercurial versioned filesystem based object storage frontend.'''

    init = 'hg://'

    def __init__(self, engine, **kw):
        super(HgStore, self).__init__(engine, **kw)
        self._repo = hgapi.Repo(self._dir)
        try:
            self._repo.hg_status()
        except Exception:
            self._repo.hg_init()

    def __setitem__(self, key, value):
        super(HgStore, self).__setitem__(key, value)
        fname = self._key_to_file(key)
        status = self._repo.hg_status()
        if fname in status['!']:
            self._repo.hg_add(fname)
            self._repo.hg_commit('added {0}'.format(fname))
        if fname in status['M']:
            self._repo.hg_commit('added {0}'.format(fname))

    def __delitem__(self, key):
        super(HgStore, self).__delitem__(key)
        fname = self._key_to_file(key)
        if fname in self._repo.hg_status()['R']:
            self._repo.hg_remove(fname)
            self._repo.hg_commit('removed {0}'.format(fname))
