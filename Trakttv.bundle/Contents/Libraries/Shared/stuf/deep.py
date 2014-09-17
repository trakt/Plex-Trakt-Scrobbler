# -*- coding: utf-8 -*-
'''stuf deep objectry.'''

from functools import partial
from operator import attrgetter, getitem

clsdict = attrgetter('__dict__')
selfname = attrgetter('__name__')
# get class of instance.
getcls = attrgetter('__class__')
clsname = lambda this: selfname(getcls(this))

# lightweight object manipulation
hasit = lambda x, y: y in clsdict(x)
getit = lambda x, y: clsdict(x)[y]
setit = lambda x, y, z: clsdict(x).__setitem__(y, z)
delit = lambda x, y: clsdict(x).__delitem__(y)


def attr_or_item(this, key):
    '''Get attribute or item `key` from `this`.'''
    try:
        return getitem(this, key)
    except (KeyError, TypeError):
        return getter(this, key)


def deepget(this, key, default=None):
    '''Get deep attribut `key` on `this`, setting it to `default` if unset.'''
    try:
        return attrgetter(key)(this)
    except AttributeError:
        return default


def deleter(this, key):
    '''Delete attribute `key` from `this`.'''
    try:
        object.__delattr__(this, key)
    except (AttributeError, TypeError):
        delattr(this, key)


def getter(this, key):
    '''Get attribute `key` from `this`.'''
    try:
        return object.__getattribute__(this, key)
    except (AttributeError, TypeError):
        return getattr(this, key)


def members(this):
    '''Iterator version of ``inspect.getmembers``.'''
    getr = partial(getattr, this)
    for key in dir(this):
        try:
            value = getr(key)
        except AttributeError:
            pass
        else:
            yield key, value


def setter(this, key, value):
    '''Set attribute `key` on `this` to value and return `value`.'''
    # it's an instance
    try:
        this.__dict__[key] = value
    # it's a class
    except TypeError:
        setattr(this, key, value)
        return value
    else:
        return value


def setthis(this, key, value):
    '''Set attribute `key` on `this` to value and return `this`.'''
    # it's an instance
    try:
        this.__dict__[key] = value
    # it's a class
    except TypeError:
        setattr(this, key, value)
        return this
    else:
        return this


def setdefault(this, key, default=None):
    '''Get attribute `key` on `this`, setting it with `default` if unset.'''
    try:
        return getter(this, key)
    except AttributeError:
        return setter(this, key, default)


def setpart(this, key, method, *args):
    '''
    Set attribute `key` on `this` to partial method and return partial method.
    '''
    part = partial(method, *args)
    try:
        this.__dict__[key] = part
    # it's a class
    except TypeError:
        setattr(this, key, part)
    else:
        return part
