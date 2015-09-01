# -*- coding: utf-8 -*-
'''stuf base.'''

import sys
from functools import partial
from keyword import iskeyword
from operator import itemgetter
from unicodedata import normalize
from importlib import import_module
from collections import Sequence, Mapping

# one frame
one = lambda a, b: a(b)
# two frame
two = lambda a, b, *args: a(b(*args))
# factory for "is" checkers
isfactory = lambda x: partial(lambda x, y, z: x(z, y), isinstance, x)
# next frame up
getframe = partial(sys._getframe, 1)
identity = lambda x: x
dualidentity = lambda x, y: (x, y)
isnone = lambda x, y: x if y is None else y
first = itemgetter(0)
second = itemgetter(1)
last = itemgetter(-1)
maporseq = isfactory((Mapping, Sequence))
ismapping = isfactory(Mapping)
issequence = isfactory(Sequence)
norm = partial(normalize, 'NFKD')
# illegal characters for Python names
ic = frozenset('()[]{}@,:`=;+*/%&|^><\'"#\\$?!~'.split())


def backport(*paths):
    '''Go through import `paths` until one imports or everything fails.'''
    load = None
    for path in paths:
        try:
            load = importer(path)
            break
        except ImportError:
            continue
    if load is None:
        raise ImportError('no path')
    return load


def checkname(name, ic=ic):
    '''Ensures `name` is legal for Python.'''
    # Remove characters that are illegal in a Python name
    name = name.strip().lower().replace('-', '_').replace(
        '.', '_'
    ).replace(' ', '_')
    name = ''.join(i for i in name if i not in ic)
    # add _ if value is Python keyword
    return name + '_' if iskeyword(name) else name


def coroutine(func):
    '''The Dave Beazley co-routine decorator.'''
    def start(*args, **kw):
        cr = func(*args, **kw)
        cr.next()
        return cr
    return start


def docit(call, doc):
    '''Add documentation to a callable.'''
    call.__doc__ = doc
    return call


def importer(path, attribute=None, i=import_module, g=getattr):
    '''Import module `path`, optionally with `attribute`.'''
    try:
        dot = path.rindex('.')
        # import module
        path = g(i(path[:dot]), path[dot + 1:])
    # If nothing but module name, import the module
    except (AttributeError, ValueError):
        path = i(path)
    if attribute:
        path = g(path, attribute)
    return path
