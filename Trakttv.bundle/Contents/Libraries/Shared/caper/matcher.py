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

from caper.helpers import update_dict, delta_seconds
from caper.objects import CaperPattern
from datetime import datetime
from logr import Logr
import caper.compat
import itertools


class Matcher(object):
    def __init__(self, pattern_groups):
        self.regex = {}

        self.construct_patterns(pattern_groups)

    def construct_patterns(self, pattern_groups):
        compile_start = datetime.now()
        compile_count = 0

        for group_name, patterns in pattern_groups:
            if group_name not in self.regex:
                self.regex[group_name] = []

            # Transform into weight groups
            if type(patterns[0]) is str or type(patterns[0][0]) not in [int, float]:
                patterns = [(1.0, patterns)]

            for weight, patterns in patterns:
                weight_patterns = []

                for pattern in [CaperPattern.construct(v) for v in patterns if v]:
                    compile_count += pattern.compile()
                    weight_patterns.append(pattern)

                self.regex[group_name].append((weight, weight_patterns))

        Logr.info("Compiled %s patterns in %ss", compile_count, delta_seconds(datetime.now() - compile_start))

    def find_group(self, name):
        for group_name, weight_groups in self.regex.items():
            if group_name and group_name == name:
                return group_name, weight_groups

        return None, None

    def value_match(self, value, group_name=None, single=True):
        result = None

        for group, weight_groups in self.regex.items():
            if group_name and group != group_name:
                continue

            # TODO handle multiple weights
            weight, patterns = weight_groups[0]

            for pattern in patterns:
                match = pattern[0].match(value)
                if not match:
                    continue

                if result is None:
                    result = {}
                if group not in result:
                    result[group] = {}

                result[group].update(match.groupdict())

                if single:
                    return result

        return result

    def fragment_match(self, fragment, group_name=None):
        """Follow a fragment chain to try find a match

        :type fragment: caper.objects.CaperFragment
        :type group_name: str or None

        :return: The weight of the match found between 0.0 and 1.0,
                  where 1.0 means perfect match and 0.0 means no match
        :rtype: (float, dict, int)
        """

        group_name, weight_groups = self.find_group(group_name)

        for weight, patterns in weight_groups:
            for pattern in patterns:
                success = True
                result = {}

                num_matched = 0

                fragment_iterator = fragment.take_right(
                    return_type='value',
                    include_separators=pattern.include_separators,
                    include_source=True
                )

                for subject, fragment_pattern in itertools.izip_longest(fragment_iterator, pattern):
                    # No patterns left to match
                    if not fragment_pattern:
                        break

                    # No fragments left to match against pattern
                    if not subject:
                        success = False
                        break

                    value, source = subject

                    matches = pattern.execute(fragment_pattern, value)

                    if matches:
                        for match in pattern.process(matches):
                            update_dict(result, match)
                    else:
                        success = False
                        break

                    if source == 'subject':
                        num_matched += 1

                if success:
                    Logr.debug('Found match with weight %s using regex pattern "%s"' % (weight, [sre.pattern for sre in pattern.patterns]))
                    return float(weight), result, num_matched

        return 0.0, None, 1
