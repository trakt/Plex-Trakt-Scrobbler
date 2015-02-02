# -*- coding: utf-8 -*-
'''
git versioned object store.

shove's URI for git-based stores follows the form:

git://<path>

Where the path is a URI path to a git repository on a local filesystem.
Alternatively, a native pathname to the repository can be passed as the
'engine' argument.
'''

try:
    from dulwich.repo import Repo
    from dulwich.errors import NotGitRepository
except ImportError:
    raise ImportError('requires dulwich library')

from shove.store import FileStore
from shove._compat import quote_plus


class GitStore(FileStore):

    '''Git versioned filesystem based object storage frontend.'''

    init = 'git://'

    def __init__(self, engine, **kw):
        super(GitStore, self).__init__(engine, **kw)
        try:
            self._repo = Repo(self._dir)
        except NotGitRepository:
            self._repo = Repo.init(self._dir)

    def __setitem__(self, key, value):
        super(GitStore, self).__setitem__(key, value)
        fname = quote_plus(key)
        self._repo.stage([fname])
        self._repo.do_commit('added {0}'.format(fname), committer='shove')

    def __delitem__(self, key):
        super(GitStore, self).__delitem__(key)
        fname = quote_plus(key)
        self._repo.stage([fname])
        self._repo.do_commit('removed {0}'.format(fname))
