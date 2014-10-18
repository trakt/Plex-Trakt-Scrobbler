# -*- coding: utf-8 -*-
'''stuf collections.'''

import sys

from .deep import getcls
from .base import second, first
from .six import OrderedDict, items

try:
    from reprlib import recursive_repr  # @UnusedImport
except ImportError:
    from .six import get_ident, getdoc, getmod, docit

    def recursive_repr(fillvalue='...'):
        def decorating_function(user_function):
            repr_running = set()
            def wrapper(self):  # @IgnorePep8
                key = id(self), get_ident()
                if key in repr_running:
                    return fillvalue
                repr_running.add(key)
                try:
                    result = user_function(self)
                finally:
                    repr_running.discard(key)
                return result
            wrapper.__module__ = getmod(user_function)
            docit(wrapper, getdoc(user_function))
            return wrapper
        return decorating_function

version = sys.version_info
if version[0] == 3 and version[1] > 1:
    from collections import Counter
else:
    from heapq import nlargest
    from itertools import chain, starmap, repeat

    from .deep import clsname
    from .base import ismapping

    class Counter(dict):

        '''dict subclass for counting hashable items'''

        def __init__(self, iterable=None, **kw):
            '''
            If given, count elements from an input iterable. Or, initialize
            count from another mapping of elements to their counts.
            '''
            super(Counter, self).__init__()
            self.update(iterable, **kw)

        def __missing__(self, key):
            '''The count of elements not in the Counter is zero.'''
            return 0

        def __reduce__(self):
            return getcls(self), (dict(self),)

        def __delitem__(self, elem):
            '''
            Like dict.__delitem__() but does not raise KeyError for missing'
            values.
            '''
            if elem in self:
                super(Counter, self).__delitem__(elem)

        def __repr__(self): # pragma: no coverage
            if not self:
                return '%s()' % clsname(self)
            try:
                items = ', '.join(map('%r: %r'.__mod__, self.most_common()))
                return '%s({%s})' % (clsname(self), items)
            except TypeError:
                # handle case where values are not orderable
                return '{0}({1!r})'.format(clsname(self), dict(self))

        def __add__(self, other):
            '''Add counts from two counters.'''
            if not isinstance(other, getcls(self)):
                return NotImplemented()
            result = getcls(self)()
            for elem, count in items(self):
                newcount = count + other[elem]
                if newcount > 0:
                    result[elem] = newcount
            for elem, count in items(other):
                if elem not in self and count > 0:
                    result[elem] = count
            return result

        def __sub__(self, other):
            '''Subtract count, but keep only results with positive counts.'''
            if not isinstance(other, getcls(self)):
                return NotImplemented()
            result = getcls(self)()
            for elem, count in items(self):
                newcount = count - other[elem]
                if newcount > 0:
                    result[elem] = newcount
            for elem, count in items(other):
                if elem not in self and count < 0:
                    result[elem] = 0 - count
            return result

        def __or__(self, other):
            '''Union is the maximum of value in either of the input counters.'''
            if not isinstance(other, getcls(self)):
                return NotImplemented()
            result = getcls(self)()
            for elem, count in items(self):
                other_count = other[elem]
                newcount = other_count if count < other_count else count
                if newcount > 0:
                    result[elem] = newcount
            for elem, count in items(other):
                if elem not in self and count > 0:
                    result[elem] = count
            return result

        def __and__(self, other):
            '''Intersection is the minimum of corresponding counts.'''
            if not isinstance(other, getcls(self)):
                return NotImplemented()
            result = getcls(self)()
            for elem, count in items(self):
                other_count = other[elem]
                newcount = count if count < other_count else other_count
                if newcount > 0:
                    result[elem] = newcount
            return result

        def __pos__(self):
            '''
            Adds an empty counter, effectively stripping negative and zero
            counts.
            '''
            return self + getcls(self)()

        def __neg__(self):
            '''
            Subtracts from an empty counter. Strips positive and zero counts,
            and flips the sign on negative counts.
            '''
            return getcls(self)() - self

        def most_common(self, n=None, nl=nlargest, i=items, g=second):
            '''
            List the n most common elements and their counts from the most
            common to the least. If n is None, then list all element counts.
            '''
            if n is None:
                return sorted(i(self), key=g, reverse=True)
            return nl(n, i(self), key=g)

        def elements(self):
            '''
            Iterator over elements repeating each as many times as its count.
            '''
            return chain.from_iterable(starmap(repeat, items(self)))

        @classmethod
        def fromkeys(cls, iterable, v=None):
            raise NotImplementedError(
                'Counter.fromkeys() undefined. Use Counter(iterable) instead.'
            )

        def update(self, iterable=None, **kwds):
            '''Like dict.update() but add counts instead of replacing them.'''
            if iterable is not None:
                if ismapping(iterable):
                    if self:
                        self_get = self.get
                        for elem, count in items(iterable):
                            self[elem] = count + self_get(elem, 0)
                    else:
                        super(Counter, self).update(iterable)
                else:
                    mapping_get = self.get
                    for elem in iterable:
                        self[elem] = mapping_get(elem, 0) + 1
            if kwds:
                self.update(kwds)

        def subtract(self, iterable=None, **kwds):
            '''
            Like dict.update() but subtracts counts instead of replacing them.
            Counts can be reduced below zero.  Both the inputs and outputs are
            allowed to contain zero and negative counts.

            Source can be an iterable, a dictionary, or another Counter
            instance.
            '''
            if iterable is not None:
                self_get = self.get
                if ismapping(iterable):
                    for elem, count in items(iterable):
                        self[elem] = self_get(elem, 0) - count
                else:
                    for elem in iterable:
                        self[elem] = self_get(elem, 0) - 1
            if kwds:
                self.subtract(kwds)

        def copy(self):
            'Return a shallow copy.'
            return getcls(self)(self)

try:
    from collections import ChainMap  # @UnusedImport
except ImportError:
    # not until Python >= 3.3
    from collections import MutableMapping

    class ChainMap(MutableMapping):

        '''
        `ChainMap` groups multiple dicts (or other mappings) together to create
        a single, updateable view.
        '''

        def __init__(self, *maps):
            '''
            Initialize `ChainMap` by setting *maps* to the given mappings. If no
            mappings are provided, a single empty dictionary is used.
            '''
            # always at least one map
            self.maps = list(maps) or [OrderedDict()]

        def __missing__(self, key):
            raise KeyError(key)

        def __getitem__(self, key):
            for mapping in self.maps:
                try:
                    # can't use 'key in mapping' with defaultdict
                    return mapping[key]
                except KeyError:
                    pass
            # support subclasses that define __missing__
            return self.__missing__(key)

        def get(self, key, default=None):
            return self[key] if key in self else default

        def __len__(self):
            # reuses stored hash values if possible
            return len(set().union(*self.maps))

        def __iter__(self, set=set):
            return set().union(*self.maps).__iter__()

        def __contains__(self, key, any=any):
            return any(key in m for m in self.maps)

        def __bool__(self, any=any):
            return any(self.maps)

        @classmethod
        def fromkeys(cls, iterable, *args):
            '''
            Create a ChainMap with a single dict created from the iterable.
            '''
            return cls(dict.fromkeys(iterable, *args))

        def copy(self):
            '''
            New ChainMap or subclass with a new copy of maps[0] and refs to
            maps[1:]
            '''
            return getcls(self)(first(self.maps).copy(), *self.maps[1:])

        __copy__ = copy

        def new_child(self):
            '''New ChainMap with a new dict followed by all previous maps.'''
            # like Django's Context.push()
            return getcls(self)({}, *self.maps)

        @property
        def parents(self):
            '''New ChainMap from maps[1:].'''
            # like Django's Context.pop()
            return getcls(self)(*self.maps[1:])

        def __setitem__(self, key, value):
            first(self.maps)[key] = value

        def __delitem__(self, key):
            try:
                del first(self.maps)[key]
            except KeyError:
                raise KeyError(
                    'Key not found in the first mapping: {r}'.format(key)
                )

        def popitem(self):
            '''
            Remove and return an item pair from maps[0]. Raise `KeyError` is
            maps[0] is empty.
            '''
            try:
                return first(self.maps).popitem()
            except KeyError:
                raise KeyError('No keys found in the first mapping.')

        def pop(self, key, *args):
            '''
            Remove *key* from maps[0] and return its value. Raise KeyError if
            *key* not in maps[0].
            '''
            try:
                return first(self.maps).pop(key, *args)
            except KeyError:
                raise KeyError(
                    'Key not found in the first mapping: {r}'.format(key)
                )

        def clear(self):
            '''Clear maps[0], leaving maps[1:] intact.'''
            first(self.maps).clear()
