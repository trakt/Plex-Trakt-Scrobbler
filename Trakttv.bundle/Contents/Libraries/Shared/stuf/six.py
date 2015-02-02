# -*- coding: utf-8 -*-
'''Utilities for writing code that runs on Python 2 and 3.'''

from stuf.base import first, docit, identity, getframe, backport, norm

import sys
import types
from functools import partial
from importlib import import_module
from operator import attrgetter, methodcaller, lt, gt

from .base import isfactory

intern = backport('__builtin__.intern', 'sys.intern')
OrderedDict = backport('collections.OrderedDict', 'ordereddict.OrderedDict')
unittest = backport('unittest2', 'unittest')
get_ident = backport(
    'thread.get_ident', 'dummy_thread.get_ident', '_thread.get_ident',
)
pickle = backport('cPickle', 'pickle')
filter = backport('future_builtins.filter', 'builtins.filter')
map = backport('future_builtins.map', 'builtins.map')
zip = backport('future_builtins.zip', 'builtins.zip')
# use next generation regular expression library if available
rcompile = backport('regex.compile', 're.compile')
rescape = backport('regex.escape', 're.escape')
rsub = backport('regex.sub', 're.sub')
subprocess = backport('subprocess32.Popen', 'subprocess.Popen')

# True if we are running on Python 3.
PY3 = first(sys.version_info) == 3

if PY3:
    strings = str,
    integers = int,
    long = int
    classes = type,
    utfme = native = texts = str
    byteme = binaries = bytes
    MAXSIZE = sys.maxsize
else:
    strings = basestring,
    integers = (int, long)
    classes = (type, types.ClassType)
    utfme = texts = unicode
    byteme = native = binaries = str
    if sys.platform == 'java':
        # Jython always uses 32 bits.
        MAXSIZE = int((1 << 31) - 1)
    else:
        # It's possible to have sizeof(long) != sizeof(Py_ssize_t).
        class X(object):
            def __len__(self):
                return 1 << 31
        try:
            len(X())
        except OverflowError:
            # 32-bit
            MAXSIZE = int((1 << 31) - 1)
        else:
            # 64-bit
            MAXSIZE = int((1 << 63) - 1)
        del X

# numbers
isgtemax = docit(partial(gt, MAXSIZE), 'Less than max size?')
isinteger = docit(isfactory(integers), 'is integer?')
isltemax = docit(partial(lt, MAXSIZE), 'Greater than max size?')
# strings
isstring = docit(isfactory(strings), 'is string')
isunicode = docit(isfactory(utfme), 'is text?')
isnative = docit(isfactory(native), 'is native string')
isbinary = isbytes = docit(isfactory(byteme), 'is binary?')


class _LazyDescr(object):

    def __init__(self, name):
        self.name = name

    def __get__(self, obj, tp):
        result = self._resolve()
        setattr(obj, self.name, result)
        # This is a bit ugly, but it avoids running this again.
        delattr(tp, self.name)
        return result


class MovedModule(_LazyDescr):

    def __init__(self, name, old, new=None):
        super(MovedModule, self).__init__(name)
        if PY3:
            if new is None:
                new = name
            self.mod = new
        else:
            self.mod = old

    def _resolve(self):
        return import_module(self.mod)


class MovedAttribute(_LazyDescr):

    def __init__(self, name, old_mod, new_mod, old_attr=None, new_attr=None):
        super(MovedAttribute, self).__init__(name)
        if PY3:
            if new_mod is None:
                new_mod = name
            self.mod = new_mod
            if new_attr is None:
                new_attr = name if old_attr is None else old_attr
            self.attr = new_attr
        else:
            self.mod = old_mod
            if old_attr is None:
                old_attr = name
            self.attr = old_attr

    def _resolve(self):
        return getattr(import_module(self.mod), self.attr)


class _MovedItems(types.ModuleType):
    '''Lazy loading of moved objects.'''


_moved_attributes = [
    MovedAttribute(
        'GeneratorContextManager',
        'contextlib',
        'contextlib',
        'GeneratorContextManager',
        '_GeneratorContextManager',
    ),
    MovedAttribute(
        'filterfalse', 'itertools', 'itertools', 'ifilterfalse', 'filterfalse',
    ),
    MovedAttribute(
        'zip_longest', 'itertools', 'itertools', 'izip_longest', 'zip_longest',
    ),
    MovedAttribute('reload_module', '__builtin__', 'imp', 'reload'),
    MovedAttribute('reduce', '__builtin__', 'functools'),
    MovedAttribute('xrange', '__builtin__', 'builtins', 'xrange', 'range'),
    MovedAttribute('parsedate_tz', 'rfc822', 'email.utils', 'parsedate_tz'),
    MovedAttribute('formatdate', 'rfc822', 'email.utils', 'formatdate'),
    MovedAttribute('parse_qs', 'cgi', 'urllib.parse', 'parse_qs'),
    MovedAttribute('urlencode', 'urllib', 'urllib.parse', 'urlencode'),
    MovedAttribute('quote', 'urllib', 'urllib.parse'),
    MovedAttribute('input', '__builtin__', 'builtins', 'raw_input', 'input'),
    MovedModule('builtins', '__builtin__'),
    MovedModule('configparser', 'ConfigParser'),
    MovedModule('copyreg', 'copy_reg'),
    MovedModule('http_cookiejar', 'cookielib', 'http.cookiejar'),
    MovedModule('http_cookies', 'Cookie', 'http.cookies'),
    MovedModule('html_entities', 'htmlentitydefs', 'html.entities'),
    MovedModule('html_parser', 'HTMLParser', 'html.parser'),
    MovedModule('http_client', 'httplib', 'http.client'),
    MovedModule('BaseHTTPServer', 'BaseHTTPServer', 'http.server'),
    MovedModule('CGIHTTPServer', 'CGIHTTPServer', 'http.server'),
    MovedModule('SimpleHTTPServer', 'SimpleHTTPServer', 'http.server'),
    MovedModule('queue', 'Queue'),
    MovedModule('reprlib', 'repr'),
    MovedModule('socketserver', 'SocketServer'),
    MovedModule('urllib_robotparser', 'robotparser', 'urllib.robotparser'),
    MovedModule('winreg', '_winreg'),
    MovedModule('xmlrpc', 'xmlrpclib', 'xmlrpc.client'),
]
for attr in _moved_attributes:
    setattr(_MovedItems, attr.name, attr)
del attr
moves = sys.modules['stuf.six.moves'] = _MovedItems('moves')


def add_move(move):
    '''Add an item to six.moves.'''
    setattr(_MovedItems, move.name, move)


def remove_move(name):
    '''Remove item from six.moves.'''
    try:
        delattr(_MovedItems, name)
    except AttributeError:
        try:
            del moves.__dict__[name]
        except KeyError:
            raise AttributeError('no such move, {r}'.format(name))

if PY3:
    _meth_func = '__func__'
    _meth_self = '__self__'
    _func_code = '__code__'
    _func_defaults = '__defaults__'
    _iterkeys = 'keys'
    _itervalues = 'values'
    _iteritems = 'items'
else:
    _meth_func = 'im_func'
    _meth_self = 'im_self'
    _func_code = 'func_code'
    _func_defaults = 'func_defaults'
    _iterkeys = 'iterkeys'
    _itervalues = 'itervalues'
    _iteritems = 'iteritems'

try:
    advance_iterator = next
except NameError:
    advance_iterator = methodcaller('next')
next = advance_iterator

if PY3:
    range = range
    unbound_function = identity
    Iterator = object
    callable = lambda o: any('__call__' in k.__dict__ for k in type(o).__mro__)
else:
    range = xrange
    callable = callable
    unbound_function = attrgetter('im_func')

    class Iterator(object):
        def next(self):
            return type(self).__next__(self)

func_code = attrgetter(_func_code)
func_defaults = attrgetter(_func_defaults)
getitems = attrgetter(_iteritems)
getkeys = attrgetter(_iterkeys)
getvalues = attrgetter(_itervalues)
items = methodcaller(_iteritems)
keys = methodcaller(_iterkeys)
method_func = attrgetter(_meth_func)
method_self = attrgetter(_meth_self)
values = methodcaller(_itervalues)
getdoc = attrgetter('__doc__')
getmod = attrgetter('__module__')

if PY3:
    b = methodcaller('encode', 'latin-1')
    u = identity
    if sys.version_info[1] <= 1:
        int2byte = partial(lambda x, i: x((i,)), bytes)
    else:
        # This is about 2x faster than the implementation above on 3.2+
        int2byte = methodcaller('to_bytes', 1, 'big')
    import io
    StringIO = io.StringIO
    BytesIO = io.BytesIO
else:
    b = identity
    u = partial(lambda x, s: x(s, 'unicode_escape'), unicode)
    int2byte = chr
    import StringIO
    StringIO = BytesIO = StringIO.StringIO

#b = docit(b, 'Byte literal.')
#u = docit(u, 'Text literal.')


if PY3:
    import builtins  # @UnresolvedImport
    exec_ = getattr(builtins, 'exec')

    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value
    printf = getattr(builtins, 'print')
    del builtins
else:
    def exec_(code, globs=None, locs=None):
        '''Execute code in a namespace.'''
        if globs is None:
            frame = getframe()
            globs = frame.f_globals
            if locs is None:
                locs = frame.f_locals
            del frame
        elif locs is None:
            locs = globs
        exec('''exec code in globs, locs''')

    exec_('def reraise(tp, value, tb=None): raise tp, value, tb')

    def printf(*args, **kw):
        '''The new-style print function.'''
        fp = kw.pop('file', sys.stdout)
        if fp is None:
            return
        def write(data):  # @IgnorePep8
            if not isstring(data):
                data = str(data)
            fp.write(data)
        want_unicode = False
        sep = kw.pop('sep', None)
        if sep is not None:
            if isunicode(sep):
                want_unicode = True
            elif not isbytes(sep):
                raise TypeError('sep must be None or a string')
        end = kw.pop('end', None)
        if end is not None:
            if isunicode(end):
                want_unicode = True
            elif not isbytes(end):
                raise TypeError('end must be None or a string')
        if kw:
            raise TypeError('invalid keyword arguments to print()')
        if not want_unicode:
            for arg in args:
                if isunicode(arg):
                    want_unicode = True
                    break
        if want_unicode:
            newline = utfme('\n')
            space = utfme(' ')
        else:
            newline = '\n'
            space = ' '
        if sep is None:
            sep = space
        if end is None:
            end = newline
        for i, arg in enumerate(args):
            if i:
                write(sep)
            write(arg)
        write(end)


def with_metaclass(meta, base=object):
    '''Create a base class with a metaclass.'''
    return meta('NewBase', (base,), {})


def tounicode(thing, encoding='utf-8', errors='strict'):
    '''Convert string `thing` to unicode string with `encoding`.'''
    if isbytes(thing):
        try:
            return thing.decode(encoding, errors)
        except UnicodeDecodeError:
            return norm(thing).decode(encoding, errors)
    elif isunicode(thing):
        return thing.encode(encoding, errors).decode(encoding, errors)
    return utfme(thing).encode(encoding, errors).decode(encoding, errors)


def tobytes(thing, encoding='utf-8', errors='strict'):
    '''Convert string `thing` to byte string `encoding`.'''
    if isbytes(thing):
        return thing
    elif isunicode(thing):
        return norm(thing).encode(encoding, errors)
    return utfme(thing).encode(encoding, errors)
