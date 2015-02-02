# -*- coding: utf-8 -*-
'''shove core.'''

from functools import partial
from os.path import exists, join
from os import listdir, remove, makedirs
from zlib import compress, decompress, error

from stuf.six import pickle
from stuf.utils import loads, optimize

from shove._compat import url2pathname, quote_plus, unquote_plus


class Base(object):

    '''Base for shove.'''

    def __init__(self, engine, **kw):
        # keyword compress True, False, or an integer compression level (1-9)
        self._compress = kw.get('compress', False)
        # pickle protocol
        protocol = kw.get('protocol', pickle.HIGHEST_PROTOCOL)
        if kw.get('optimize', False):
            self._optimizer = partial(optimize, p=protocol)
        else:
            self._optimizer = partial(pickle.dumps, protocol=protocol)

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def dumps(self, value):
        '''Optionally serializes and compresses object `value`.'''
        # serialize anything but ASCII strings
        value = self._optimizer(value)
        compression = self._compress
        if compression:
            value = compress(value, 9 if compression is True else compression)
        return value

    def loads(self, value):
        '''Deserializes and optionally decompresses object `value`.'''
        if self._compress:
            try:
                value = decompress(value)
            except error:
                pass
        return loads(value)


class Mapping(Base):

    '''Base mapping for shove.'''

    def __getitem__(self, key):
        try:
            return self._store[key]
        except KeyError:
            raise KeyError(key)

    def __setitem__(self, key, value):
        self._store[key] = value

    def __delitem__(self, key):
        try:
            del self._store[key]
        except KeyError:
            raise KeyError(key)

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)


class FileBase(Base):

    '''Base for file based storage.'''

    def __init__(self, engine, **kw):
        super(FileBase, self).__init__(engine, **kw)
        if engine.startswith(self.init):
            engine = url2pathname(engine.split('://')[1])
        self._dir = engine
        # Create directory
        if not exists(self._dir):
            self._createdir()

    def __getitem__(self, key):
        # (per Larry Meyn)
        try:
            with open(self._key_to_file(key), 'rb') as item:
                return self.loads(item.read())
        except (IOError, OSError):
            raise KeyError(key)

    def __setitem__(self, key, value):
        # (per Larry Meyn)
        try:
            with open(self._key_to_file(key), 'wb') as item:
                item.write(self.dumps(value))
        except (IOError, OSError):
            raise KeyError(key)

    def __delitem__(self, key):
        try:
            remove(self._key_to_file(key))
        except (IOError, OSError):
            raise KeyError(key)

    def __iter__(self, unquote_plus=unquote_plus):
        for name in listdir(self._dir):
            if not name.startswith('.'):
                yield unquote_plus(name)

    def __contains__(self, key):
        return exists(self._key_to_file(key))

    def __len__(self):
        return len([i for i in listdir(self._dir) if not i.startswith('.')])

    def _createdir(self):
        # creates the store directory
        try:
            makedirs(self._dir)
        except OSError:
            raise EnvironmentError(
                'cache directory "{0}" does not exist and could not be '
                'created'.format(self._dir)
            )

    def _key_to_file(self, key):
        # gives the filesystem path for a key
        return join(self._dir, quote_plus(key))
