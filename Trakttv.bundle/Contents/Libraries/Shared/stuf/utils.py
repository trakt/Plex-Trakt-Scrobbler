# -*- coding: utf-8 -*-
'''stuf utilities.'''

from uuid import uuid4
from threading import Lock
from pickletools import genops
from itertools import count, repeat
from functools import update_wrapper, partial

from .base import importer, first, norm
from .six import (
    PY3, items, isstring, func_code, b, next, intern, rcompile, pickle, u)

# first slug pattern
one = partial(rcompile(r'[^\w\s-]').sub, '')
# second slug pattern
two = partial(rcompile(r'[-\s]+').sub, '-')
# counter
count = partial(next, count())
# light weight  range
lrange = partial(repeat, None)
# unique identifier selection
unique_id = lambda: b(uuid4().hex.upper())
# return one or all values
oneorall = lambda value: value[0] if len(value) == 1 else value


def diff(current, past):
    '''Difference between `past` and `current` ``dicts``.'''
    intersect = set(current).intersection(set(past))
    changed = set(o for o in intersect if past[o] != current[o])
    return dict((k, v) for k, v in items(current) if k in changed)


def lazyimport(path, attribute=None, i=importer, s=isstring):
    '''
    Deferred module loader.

    :argument path: something to load
    :keyword str attribute: attribute on loaded module to return
    '''
    return importer(path, attribute) if s(path) else path

# import loader
lazyload = partial(
    lambda y, z, x: y(x) if z(x) and '.' in x else x,
    lazyimport,
    isstring,
)


def lru(maxsize=100):
    '''
    Least-recently-used cache decorator.

    If *maxsize* is set to None, the LRU features are disabled and the cache
    can grow without bound.

    Arguments to the cached function must be hashable.

    Access the underlying function with f.__wrapped__.

    See:  http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    By Raymond Hettinger
    '''
    def decorator(call):
        cache = dict()
        items_ = items
        repr_ = repr
        intern_ = intern
        # bound method to lookup key or return None
        cache_get = cache.get
        # localize the global len() function
        len_ = len
        # because linkedlist updates aren't threadsafe
        lock = Lock()
        # root of the circular doubly linked list
        root = []
        # make updateable non-locally
        nonlocal_root = [root]
        # initialize by pointing to self
        root[:] = [root, root, None, None]
        # names for the link fields
        PREV, NEXT, KEY, RESULT = 0, 1, 2, 3
        if maxsize is None:
            def wrapper(*args, **kw):
                # simple caching without ordering or size limit
                key = repr_(args, items_(kw)) if kw else repr_(args)
                # root used here as a unique not-found sentinel
                result = cache_get(key, root)
                if result is not root:
                    return result
                result = call(*args, **kw)
                cache[intern_(key)] = result
                return result
        else:
            def wrapper(*args, **kw):
                # size limited caching that tracks accesses by recency
                key = repr_(args, items_(kw)) if kw else repr_(args)
                with lock:
                    link = cache_get(key)
                    if link is not None:
                        # record recent use of the key by moving it to the
                        # front of the list
                        root, = nonlocal_root
                        link_prev, link_next, key, result = link
                        link_prev[NEXT] = link_next
                        link_next[PREV] = link_prev
                        last = root[PREV]
                        last[NEXT] = root[PREV] = link
                        link[PREV] = last
                        link[NEXT] = root
                        return result
                result = call(*args, **kw)
                with lock:
                    root = first(nonlocal_root)
                    if len_(cache) < maxsize:
                        # put result in a new link at the front of the list
                        last = root[PREV]
                        link = [last, root, key, result]
                        cache[intern_(key)] = last[NEXT] = root[PREV] = link
                    else:
                        # use root to store the new key and result
                        root[KEY] = key
                        root[RESULT] = result
                        cache[intern_(key)] = root
                        # empty the oldest link and make it the new root
                        root = nonlocal_root[0] = root[NEXT]
                        del cache[root[KEY]]
                        root[KEY] = None
                        root[RESULT] = None
                return result
        def clear():
            # clear the cache and cache statistics
            with lock:
                cache.clear()
                root = first(nonlocal_root)
                root[:] = [root, root, None, None]
        wrapper.__wrapped__ = call
        wrapper.clear = clear
        try:
            return update_wrapper(wrapper, call)
        except AttributeError:
            return wrapper
    return decorator


def memoize(f, i=intern, z=items, r=repr, uw=update_wrapper):
    '''Memoize function.'''
    f.cache = {}.setdefault
    if func_code(f).co_argcount == 1:
        memoize_ = lambda arg: f.cache(i(r(arg)), f(arg))
    else:
        def memoize_(*args, **kw):  # @IgnorePep8
            return f.setdefault(
                i(r(args, z(kw)) if kw else r(args)), f(*args, **kw)
            )
    return uw(f, memoize_)


def optimize(
    obj,
    S=StopIteration,
    b_=b,
    d=pickle.dumps,
    g=genops,
    n=next,
    p=pickle.HIGHEST_PROTOCOL,
    s=set,
):
    '''
    Optimize a pickle string by removing unused PUT opcodes.

    Raymond Hettinger Python cookbook recipe # 545418
    '''
    # set of args used by a GET opcode
    this = d(obj, p)
    gets = s()
    # (arg, startpos, stoppos) for the PUT opcodes set to pos if previous
    # opcode was a PUT
    def iterthing(gadd=gets.add, this=this, g=g, n=n):  # @IgnorePep8
        prevpos, prevarg = None, None
        try:
            nextr = g(this)
            while 1:
                opcode, arg, pos = n(nextr)
                if prevpos is not None:
                    yield prevarg, prevpos, pos
                    prevpos = None
                if 'PUT' in opcode.name:
                    prevarg, prevpos = arg, pos
                elif 'GET' in opcode.name:
                    gadd(arg)
        except S:
            pass
    # copy the pickle string except for PUTS without a corresponding GET
    def iterthingy(iterthing=iterthing(), this=this, n=n):  # @IgnorePep8
        i = 0
        try:
            while 1:
                arg, start, stop = n(iterthing)
                yield this[i:stop if (arg in gets) else start]
                i = stop
        except S:
            pass
        yield this[i:]
    return b_('').join(iterthingy())

moptimize = memoize(optimize)

if PY3:
    ld = loads = memoize(lambda x: pickle.loads(x, encoding='latin-1'))

    def sluggify(value, n=norm, o=one, t=two):
        '''
        Normalize `value`, convert to lowercase, remove non-alpha characters,
        and convert spaces to hyphens.
        '''
        return t(o(n(value)).strip().lower())
else:
    ld = loads = memoize(lambda x: pickle.loads(x))

    def sluggify(value, n=norm, o=one, t=two):
        '''
        Normalize `value`, convert to lowercase, remove non-alpha characters,
        and convert spaces to hyphens.
        '''
        return t(u(o(n(u(value)).encode('ascii', 'ignore')).strip().lower()))
