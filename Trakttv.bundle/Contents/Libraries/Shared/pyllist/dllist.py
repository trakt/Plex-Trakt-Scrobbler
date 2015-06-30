#!/usr/bin/env python
# -*- coding: utf-8 -*-


class dllistnode(object):
    __slots__ = ('__prev', '__next', 'value', '__list')

    def __init__(self, value=None, prev=None, next=None, list=None):
        if isinstance(value, dllistnode):
            value = value.value

        self.__prev = prev
        self.__next = next
        self.value = value
        self.__list = list

        if prev is not None:
            prev.__next = self
        if next is not None:
            next.__prev = self

    @property
    def prev(self):
        return self.__prev

    @property
    def next(self):
        return self.__next

    @property
    def list(self):
        return self.__list

    def _iter(self, direction, to=None):
        if to is not None:
            if not isinstance(to, dllistnode):
                raise TypeError('to argument must be a dllistnode')
            if to.list is not self.__list:
                raise ValueError('to argument belongs to another list')

        current = self
        while current is not None and current != to:
            yield current
            current = direction(current)

    def iternext(self, to=None):
        return self._iter(lambda x: x.__next, to=to)

    def iterprev(self, to=None):
        return self._iter(lambda x: x.__prev, to=to)

    def __call__(self):
        return self.value

    def __str__(self):
        return 'dllistnode(' + str(self.value) + ')'

    def __repr__(self):
        return '<dllistnode(' + repr(self.value) + ')>'


class dllist(object):
    __slots__ = ('__first', '__last', '__size',
                 '__last_access_node', '__last_access_idx')

    def __init__(self, sequence=None):
        self.__first = None
        self.__last = None
        self.__size = 0
        self.__last_access_node = None
        self.__last_access_idx = -1

        if sequence is None:
            return

        for value in sequence:
            node = dllistnode(value, self.__last, None, self)

            if self.__first is None:
                self.__first = node
            self.__last = node
            self.__size += 1

    @property
    def first(self):
        return self.__first

    @property
    def last(self):
        return self.__last

    @property
    def size(self):
        return self.__size

    def nodeat(self, index):
        if not isinstance(index, int):
            raise TypeError('invalid index type')

        if index < 0:
            index = self.__size + index

        if index < 0 or index >= self.__size:
            raise IndexError('index out of range')

        middle = index / 2
        if index <= middle:
            node = self.__first
            start_idx = 0
            reverse_dir = False
        else:
            node = self.__last
            start_idx = self.__size - 1
            reverse_dir = True

        if self.__last_access_node is not None and \
                self.__last_access_idx >= 0 and \
                abs(index - self.__last_access_idx) < middle:
            node = self.__last_access_node
            start_idx = self.__last_access_idx
            if index < start_idx:
                reverse_dir = True
            else:
                reverse_dir = False

        if not reverse_dir:
            while start_idx < index:
                node = node.next
                start_idx += 1
        else:
            while start_idx > index:
                node = node.prev
                start_idx -= 1

        self.__last_access_node = node
        self.__last_access_idx = index

        return node

    def appendleft(self, x):
        node = dllistnode(x, None, self.__first, self)

        if self.__last is None:
            self.__last = node
        self.__first = node
        self.__size += 1

        if self.__last_access_idx >= 0:
            self.__last_access_idx += 1
        return node

    def appendright(self, x):
        node = dllistnode(x, self.__last, None, self)

        if self.__first is None:
            self.__first = node
        self.__last = node
        self.__size += 1

        return node

    def append(self, x):
        return self.appendright(x)

    def insert(self, x, before=None, after=None):
        if after is not None:
            if before is not None:
                raise ValueError('Only before or after argument can be defined')
            before = after.next

        if before is None:
            return self.appendright(x)

        if not isinstance(before, dllistnode):
            raise TypeError('before/after argument must be a dllistnode')

        if before.list is not self:
            raise ValueError('before/after argument belongs to another list')

        node = dllistnode(x, before.prev, before, self)

        if before is self.__first:
            self.__first = node
        self.__size += 1

        self.__last_access_node = None
        self.__last_access_idx = -1

        return node

    def popleft(self):
        if self.__first is None:
            raise ValueError('list is empty')

        node = self.__first
        self.__first = node.next
        if self.__last is node:
            self.__last = None
        self.__size -= 1

        if node.prev is not None:
            node.prev._dllistnode__next = node.next
        if node.next is not None:
            node.next._dllistnode__prev = node.prev

        if self.__last_access_node is not node:
            if self.__last_access_idx >= 0:
                self.__last_access_idx -= 1
        else:
            self.__last_access_node = None
            self.__last_access_idx = -1

        return node.value

    def popright(self):
        if self.__last is None:
            raise ValueError('list is empty')

        node = self.__last
        self.__last = node.prev
        if self.__first is node:
            self.__first = None
        self.__size -= 1

        if node.prev is not None:
            node.prev._dllistnode__next = node.next
        if node.next is not None:
            node.next._dllistnode__prev = node.prev

        if self.__last_access_node is node:
            self.__last_access_node = None
            self.__last_access_idx = -1

        return node.value

    def pop(self):
        return self.popright()

    def remove(self, node):
        if not isinstance(node, dllistnode):
            raise TypeError('node argument must be a dllistnode')

        if self.__first is None:
            raise ValueError('list is empty')

        if node.list is not self:
            raise ValueError('node argument belongs to another list')

        if self.__first is node:
            self.__first = node.next
        if self.__last is node:
            self.__last = node.prev
        self.__size -= 1

        if node.prev is not None:
            node.prev._dllistnode__next = node.next
        if node.next is not None:
            node.next._dllistnode__prev = node.prev

        self.__last_access_node = None
        self.__last_access_idx = -1

        return node.value

    def iternodes(self, to=None):
        if self.__first is not None:
            return self.__first.iternext(to=to)
        else:
            return iter([])

    def __len__(self):
        return self.__size

    def __cmp__(self, other):
        result = len(self) - len(other)
        if result < 0:
            return -1
        elif result > 0:
            return 1

        for sval, oval in zip(self, other):
            result = cmp(sval, oval)
            if result != 0:
                return result

        return 0

    def __str__(self):
        if self.__first is not None:
            return 'dllist([' + ', '.join((str(x) for x in self)) + '])'
        else:
            return 'dllist()'

    def __repr__(self):
        if self.__first is not None:
            return 'dllist([' + ', '.join((repr(x) for x in self)) + '])'
        else:
            return 'dllist()'

    def __iter__(self):
        current = self.__first
        while current is not None:
            yield current.value
            current = current.next

    def __reversed__(self):
        current = self.__last
        while current is not None:
            yield current.value
            current = current.prev

    def __getitem__(self, index):
        return self.nodeat(index).value

    def __setitem__(self, index, value):
        self.nodeat(index).value = value

    def __delitem__(self, index):
        node = self.nodeat(index)
        self.remove(node)

        if node.prev is not None and index > 0:
            self.__last_access_node = node.prev
            self.__last_access_idx = index - 1

    def __add__(self, sequence):
        new_list = dllist(self)

        for value in sequence:
            new_list.append(value)

        return new_list

    def __iadd__(self, sequence):
        if sequence is not self:
            for value in sequence:
                self.append(value)
        else:
            # slower path which avoids endless loop
            # when extending list with itself
            node = sequence.__first
            last_node = self.__last
            while node is not None:
                self.append(node.value)
                if node is last_node:
                    break
                node = node.next

        return self

    def __mul__(self, count):
        if not isinstance(count, int):
            raise TypeError('count must be an integer')

        new_list = dllist()
        for i in xrange(count):
            new_list += self

        return new_list

    def __hash__(self):
        h = 0

        for value in self:
            h ^= hash(value)

        return h
