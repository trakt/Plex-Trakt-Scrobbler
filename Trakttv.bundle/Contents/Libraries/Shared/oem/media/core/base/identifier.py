from __future__ import absolute_import, division, print_function


class Identifier(object):
    @property
    def valid(self):
        return False

    def to_dict(self):
        raise NotImplementedError

    def to_frozenset(self, data=None):
        if data is None:
            data = self.to_dict()

        if type(data) is dict:
            data = data.items()

        result = []

        for item in data:
            if type(item) is tuple and len(item) == 2:
                key, value = item
            else:
                key = None
                value = item

            if type(value) is dict:
                value = self.to_frozenset(value)

            if type(value) is list:
                value = self.to_frozenset(value)

            if key is not None:
                result.append((key, value))
            else:
                result.append(value)

        return frozenset(result)

    def __hash__(self):
        return hash(self.to_frozenset())

    def __eq__(self, other):
        if not other:
            return False

        return self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not(self == other)
