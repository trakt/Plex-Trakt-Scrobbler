# -*- coding: utf-8 -*-
'''stuf descriptors.'''

from threading import local
from functools import update_wrapper, partial

from .six import items
from .iterable import exhaustmap
from .deep import selfname, setter, getcls, setpart


class lazybase(object):

    '''Base class for lazy descriptors.'''


class _lazyinit(lazybase):

    '''Base initializer for lazy descriptors.'''

    def __init__(self, method, _wrap=update_wrapper):
        super(_lazyinit, self).__init__()
        self.method = method
        self.name = selfname(method)
        _wrap(self, method)

    def _set(self, this):
        return setter(this, self.name, self.method(this))


class lazy(_lazyinit):

    '''Lazily assign attributes on an instance upon first use.'''

    def __get__(self, this, that):
        return self if this is None else self._set(this)


class lazy_class(_lazyinit):

    '''Lazily assign attributes on an class upon first use.'''

    def __get__(self, this, that):
        return self._set(that)


class lazypartial(lazy):

    '''Lazily assign attributes on an instance upon first use.'''

    def _set(self, this):
        return setter(this, self.name, partial(*self.method(this)))


class lazyset(lazy):

    '''Lazily assign attributes with a custom setter.'''

    def __init__(self, method, fget=None, _wrap=update_wrapper):
        super(lazyset, self).__init__(method)
        self.fget = fget
        _wrap(self, method)

    def __set__(self, this, value):
        self.fget(this, value)

    def __delete__(self, this):
        del this.__dict__[self.name]

    def setter(self, func):
        self.fget = func
        return self


class bothbase(_lazyinit):

    '''Base for two-way lazy descriptors.'''

    def __init__(self, method, expr=None, _wrap=update_wrapper):
        super(bothbase, self).__init__(method)
        self.expr = expr or method
        _wrap(self, method)

    def expression(self, expr):
        '''
        Modifying decorator that defines a general method.
        '''
        self.expr = expr
        return self


class both(bothbase):

    '''
    Descriptor that caches results of instance-level results while allowing
    class-level results.
    '''

    def __get__(self, this, that):
        return self.expr(that) if this is None else self._set(this)


class either(bothbase):

    '''
    Descriptor that caches results of both instance- and class-level results.
    '''

    def __get__(self, this, that):
        if this is None:
            return setter(that, self.name, self.expr(that))
        return self._set(this)


class twoway(bothbase):

    '''Descriptor that enables instance and class-level results.'''

    def __get__(self, this, that):
        return self.expr(that) if this is None else self.method(this)


class readonly(lazybase):

    '''Read-only lazy descriptor.'''

    def __set__(self, this, value):
        raise AttributeError('attribute is read-only')

    def __delete__(self, this):
        raise AttributeError('attribute is read-only')


class ResetMixin(local):

    '''Mixin for reseting descriptors subclassing :class:`lazybase`\.'''

    def reset(self):
        '''Reset previously accessed :class:`lazybase` attributes.'''
        attrs = set(vars(self))
        exhaustmap(
            delattr,
            items(vars(getcls(self))),
            lambda x, y: x in attrs and isinstance(y, lazybase),
        )


class ContextMixin(ResetMixin):

    '''Resetable context manager mixin.'''

    def __enter__(self):
        return self


class Setter(object):

    '''Partial setter.'''

    @lazypartial
    def _setter(self):
        return setpart, self
