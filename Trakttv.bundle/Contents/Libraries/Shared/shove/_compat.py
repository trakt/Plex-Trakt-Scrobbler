# -*- coding: utf-8 -*-
'''shove compatibility shim for different python versions.'''

from stuf.six import PY3
from stuf.base import backport

anydbm = backport('anydbm', 'dbm')
url2pathname = backport('urllib.url2pathname', 'urllib.request.url2pathname')
urlsplit = backport('urlparse.urlsplit', 'urllib.parse.urlsplit')
quote_plus = backport('urllib.quote_plus', 'urllib.parse.quote_plus')
unquote_plus = backport('urllib.unquote_plus', 'urllib.parse.unquote_plus')
StringIO = backport('stuf.six.moves.StringIO')


def synchronized(func):
    '''
    Decorator to lock and unlock a method (Phillip J. Eby).

    :argument func: method to decorate
    '''
    def wrapper(self, *__args, **__kw):
        self._lock.acquire()
        try:
            return func(self, *__args, **__kw)
        finally:
            self._lock.release()
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper


def openit(path, mode, encoding='utf-8'):
    return open(path, mode, encoding=encoding) if PY3 else open(path, mode)
