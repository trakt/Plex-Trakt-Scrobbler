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

ROMAN_NUMERAL_KEY = {
    "i": 1,
    "v": 5,
    "x": 10,
    "l": 50,
    "c": 100,
    "d": 500,
    "m": 1000,
}


class RomanNumerals(object):
    @classmethod
    def transform(cls, matches, key):
        for match in matches:
            if key not in match:
                continue

            match[key] = cls.convert(match[key])

        return matches

    @classmethod
    def convert(cls, value):
        total = 0

        while value:
            first_digit = cls.to_number(value[0])
            if len(value) > 1:
                second_digit = cls.to_number(value[1])
            else:
                second_digit = -1
            if first_digit >= second_digit:
                total = total + first_digit
                value = value[1:]
            else:
                total = total + (second_digit - first_digit)
                value = value[2:]

        return total

    @staticmethod
    def to_number(n):
        return ROMAN_NUMERAL_KEY[str.lower(n)]
