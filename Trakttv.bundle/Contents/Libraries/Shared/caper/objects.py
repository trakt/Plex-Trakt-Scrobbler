# Copyright 2013 Dean Gardiner <gardiner91@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from logr import Logr

from caper.helpers import is_list_type
from caper.compat import basestring
import re


class CaperSubject(object):
    def __init__(self, value=None):
        if value is None:
            value = ""

        #: :type: str
        self.value = value

    def take(self, direction, count=None, return_type='subject', include_self=True,
             include_separators=False, include_source=False):
        if direction not in ['left', 'right']:
            raise ValueError('Un-Expected value for "direction", expected "left" or "right".')

        def get_item(value):
            source = None

            if isinstance(value, basestring):
                source = 'separator'

            if isinstance(value, CaperSubject):
                source = 'subject'

                if return_type == 'value':
                    value = value.value

            if include_source:
                return value, source

            return value

        if include_self:
            yield get_item(self)

            if count:
                count -= 1

        cur = self
        n = 0

        while count is None or n < count:
            if cur and getattr(cur, direction):
                cur = getattr(cur, direction)

                if include_separators and hasattr(cur, 'left_sep'):
                    yield get_item(cur.left_sep)

                yield get_item(cur)
            else:
                break

            n += 1

    def take_left(self, count=None, **kwargs):
        return self.take('left', count, **kwargs)

    def take_right(self, count=None, **kwargs):
        return self.take('right', count, **kwargs)


class CaperClosure(CaperSubject):
    __key__ = 'closure'

    def __init__(self, index, value):
        super(CaperClosure, self).__init__(value)

        #: :type: int
        self.index = index

        #: :type: CaperClosure
        self.left = None
        #: :type: CaperClosure
        self.right = None

        #: :type: list of CaperFragment
        self.fragments = []

    def __str__(self):
        return "<CaperClosure value: %s" % repr(self.value)

    def __repr__(self):
        return self.__str__()


class CaperFragment(CaperSubject):
    __key__ = 'fragment'

    def __init__(self, closure=None):
        super(CaperFragment, self).__init__()

        #: :type: CaperClosure
        self.closure = closure

        #: :type: CaperFragment
        self.left = None
        #: :type: str
        self.left_sep = None

        #: :type: CaperFragment
        self.right = None
        #: :type: str
        self.right_sep = None

        #: :type: int
        self.position = None

    def __str__(self):
        return "<CaperFragment value: %s>" % repr(self.value)

    def __repr__(self):
        return self.__str__()


class CaptureMatch(object):
    def __init__(self, tag, step, success=False, weight=None, result=None, num_fragments=1):
        #: :type: bool
        self.success = success

        #: :type: float
        self.weight = weight

        #: :type: dict or str
        self.result = result

        #: :type: int
        self.num_fragments = num_fragments

        #: :type: str
        self.tag = tag

        #: :type: CaptureStep
        self.step = step

    def __str__(self):
        return "<CaperMatch result: %s>" % repr(self.result)

    def __repr__(self):
        return self.__str__()


class CaperPattern(object):
    def __init__(self, patterns, method='match', transform=None, include_separators=False):
        self.patterns = patterns

        self.method = method
        self.transform = transform
        self.include_separators = include_separators

    def compile(self):
        patterns = self.patterns
        self.patterns = []

        for pattern in patterns:
            if type(pattern) is tuple:
                if len(pattern) == 2:
                    # Construct OR-list pattern
                    pattern = pattern[0] % '|'.join(pattern[1])
                elif len(pattern) == 1:
                    pattern = pattern[0]

            # Compile the pattern
            try:
                self.patterns.append(re.compile(pattern, re.IGNORECASE))
            except Exception as ex:
                Logr.error('Unable to compile pattern "%s"', pattern)
                raise ex

        return len(patterns)

    def execute(self, fragment_pattern, value):
        if self.method == 'match':
            match = fragment_pattern.match(value)
            return [match] if match else []
        elif self.method == 'findall':
            return list(fragment_pattern.finditer(value))

        raise ValueError('Unknown pattern method "%s"' % self.method)

    def process(self, matches):
        matches = [match.groupdict() for match in matches]

        if self.transform:
            try:
                return self.transform(matches)
            except Exception as ex:
                Logr.warn('Exception raised while transforming matches: %s', ex)

        return matches

    def __getitem__(self, index):
        return self.patterns[index]

    def __len__(self):
        return len(self.patterns)

    def __iter__(self):
        return iter(self.patterns)

    @staticmethod
    def construct(value):
        if type(value) is CaperPattern:
            return value

        # Transform into multi-fragment patterns
        if isinstance(value, basestring):
            return CaperPattern((value,))

        if type(value) is tuple:
            if len(value) == 2 and type(value[0]) is str and is_list_type(value[1], str):
                return CaperPattern((value,))
            else:
                return CaperPattern(value)

        raise ValueError("Unknown pattern format")
