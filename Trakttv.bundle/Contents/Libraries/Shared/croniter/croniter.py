#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function
import re
from time import time
import datetime
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzutc

step_search_re = re.compile(r'^([^-]+)-([^-/]+)(/(.*))?$')
search_re = re.compile(r'^([^-]+)-([^-/]+)(/(.*))?$')
only_int_re = re.compile(r'^\d+$')
any_int_re = re.compile(r'^\d+')
star_or_int_re = re.compile(r'^(\d+|\*)$')


class CroniterBadCronError(ValueError):
    '''.'''


class CroniterBadDateError(ValueError):
    '''.'''


class CroniterNotAlphaError(ValueError):
    '''.'''


class croniter(object):
    MONTHS_IN_YEAR = 12
    RANGES = (
        (0, 59),
        (0, 23),
        (1, 31),
        (1, 12),
        (0, 6),
        (0, 59)
    )
    DAYS = (
        31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
    )

    ALPHACONV = (
        {},
        {},
        {"l": "l"},
        {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
         'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12},
        {'sun': 0, 'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6},
        {}
    )

    LOWMAP = (
        {},
        {},
        {0: 1},
        {0: 1},
        {7: 0},
        {},
    )

    bad_length = 'Exactly 5 or 6 columns has to be specified for iterator' \
                 'expression.'

    def __init__(self, expr_format, start_time=None, ret_type=float):
        self._ret_type = ret_type
        if start_time is None:
            start_time = time()

        self.tzinfo = None
        if isinstance(start_time, datetime.datetime):
            self.tzinfo = start_time.tzinfo
            start_time = self._datetime_to_timestamp(start_time)

        self.cur = start_time
        self.exprs = expr_format.split()

        if len(self.exprs) != 5 and len(self.exprs) != 6:
            raise CroniterBadCronError(self.bad_length)

        expanded = []

        for i, expr in enumerate(self.exprs):
            e_list = expr.split(',')
            res = []

            while len(e_list) > 0:
                e = e_list.pop()
                t = re.sub(r'^\*(\/.+)$', r'%d-%d\1' % (
                    self.RANGES[i][0],
                    self.RANGES[i][1]),
                    str(e))
                m = search_re.search(t)

                if not m:
                    t = re.sub(r'^(.+)\/(.+)$', r'\1-%d/\2' % (
                        self.RANGES[i][1]),
                        str(e))
                    m = step_search_re.search(t)

                if m:
                    (low, high, step) = m.group(1), m.group(2), m.group(4) or 1

                    if not any_int_re.search(low):
                        low = "{0}".format(self._alphaconv(i, low))

                    if not any_int_re.search(high):
                        high = "{0}".format(self._alphaconv(i, high))

                    if (
                        not low or not high or int(low) > int(high)
                        or not only_int_re.search(str(step))
                    ):
                        raise CroniterBadDateError(
                            "[{0}] is not acceptable".format(expr_format))

                    low, high, step = map(int, [low, high, step])
                    e_list += range(low, high + 1, step)
                    # other solution
                    #try:
                    #    for j in xrange(int(low), int(high) + 1):
                    #        if j % int(step) == 0:
                    #            e_list.append(j)
                    #except NameError:
                    #    for j in range(int(low), int(high) + 1):
                    #        if j % int(step) == 0:
                    #            e_list.append(j)
                else:
                    if t.startswith('-'):
                        raise CroniterBadCronError(
                            "[{0}] is not acceptable, negative numbers not allowed".format(
                                expr_format))
                    if not star_or_int_re.search(t):
                        t = self._alphaconv(i, t)

                    try:
                        t = int(t)
                    except:
                        pass

                    if t in self.LOWMAP[i]:
                        t = self.LOWMAP[i][t]

                    if (
                        t not in ["*", "l"]
                        and (int(t) < self.RANGES[i][0] or
                             int(t) > self.RANGES[i][1])
                    ):
                        raise CroniterBadCronError(
                            "[{0}] is not acceptable, out of range".format(
                                expr_format))

                    res.append(t)

            res.sort()
            expanded.append(['*'] if (len(res) == 1
                                      and res[0] == '*')
                            else res)
        self.expanded = expanded

    def _alphaconv(self, index, key):
        try:
            return self.ALPHACONV[index][key.lower()]
        except KeyError:
            raise CroniterNotAlphaError(
                "[{0}] is not acceptable".format(" ".join(self.exprs)))

    def get_next(self, ret_type=None):
        return self._get_next(ret_type or self._ret_type, is_prev=False)

    def get_prev(self, ret_type=None):
        return self._get_next(ret_type or self._ret_type, is_prev=True)

    def get_current(self, ret_type=None):
        ret_type = ret_type or self._ret_type
        if issubclass(ret_type,  datetime.datetime):
            return self._timestamp_to_datetime(self.cur)
        return self.cur

    def _datetime_to_timestamp(self, d):
        """
        Converts a `datetime` object `d` into a UNIX timestamp.
        """
        if d.tzinfo is not None:
            d = d.replace(tzinfo=None) - d.utcoffset()

        return self._timedelta_to_seconds(d - datetime.datetime(1970, 1, 1))

    def _timestamp_to_datetime(self, timestamp):
        """
        Converts a UNIX timestamp `timestamp` into a `datetime` object.
        """
        result = datetime.datetime.utcfromtimestamp(timestamp)
        if self.tzinfo:
            result = result.replace(tzinfo=tzutc()).astimezone(self.tzinfo)

        return result

    @classmethod
    def _timedelta_to_seconds(cls, td):
        """
        Converts a 'datetime.timedelta' object `td` into seconds contained in
        the duration.
        Note: We cannot use `timedelta.total_seconds()` because this is not
        supported by Python 2.6.
        """
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) \
            / 10**6

    # iterator protocol, to enable direct use of croniter
    # objects in a loop, like "for dt in croniter('5 0 * * *'): ..."
    # or for combining multiple croniters into single
    # dates feed using 'itertools' module
    def __iter__(self):
        return self
    __next__ = next = get_next

    def all_next(self, ret_type=None):
        '''Generator of all consecutive dates. Can be used instead of
        implicit call to __iter__, whenever non-default
        'ret_type' has to be specified.
        '''
        while True:
            yield self._get_next(ret_type or self._ret_type, is_prev=False)

    def all_prev(self, ret_type=None):
        '''Generator of all previous dates.'''
        while True:
            yield self._get_next(ret_type or self._ret_type, is_prev=True)

    iter = all_next  # alias, you can call .iter() instead of .all_next()

    def _get_next(self, ret_type=None, is_prev=False):
        expanded = self.expanded[:]

        ret_type = ret_type or self._ret_type

        if not issubclass(ret_type, (float, datetime.datetime)):
            raise TypeError("Invalid ret_type, only 'float' or 'datetime' "
                            "is acceptable.")

        if expanded[2][0] != '*' and expanded[4][0] != '*':
            bak = expanded[4]
            expanded[4] = ['*']
            t1 = self._calc(self.cur, expanded, is_prev)
            expanded[4] = bak
            expanded[2] = ['*']

            t2 = self._calc(self.cur, expanded, is_prev)
            if not is_prev:
                result = t1 if t1 < t2 else t2
            else:
                result = t1 if t1 > t2 else t2
        else:
            result = self._calc(self.cur, expanded, is_prev)
        self.cur = result

        if issubclass(ret_type, datetime.datetime):
            result = self._timestamp_to_datetime(result)

        return result

    def _calc(self, now, expanded, is_prev):
        if is_prev:
            nearest_diff_method = self._get_prev_nearest_diff
            sign = -1
        else:
            nearest_diff_method = self._get_next_nearest_diff
            sign = 1

        offset = len(expanded) == 6 and 1 or 60
        dst = now = self._timestamp_to_datetime(now + sign * offset)

        day, month, year = dst.day, dst.month, dst.year
        current_year = now.year
        DAYS = self.DAYS

        def proc_month(d):
            if expanded[3][0] != '*':
                diff_month = nearest_diff_method(
                    d.month, expanded[3], self.MONTHS_IN_YEAR)
                days = DAYS[month - 1]
                if month == 2 and self.is_leap(year) is True:
                    days += 1

                reset_day = 1

                if diff_month is not None and diff_month != 0:
                    if is_prev:
                        d += relativedelta(months=diff_month)
                        reset_day = DAYS[d.month - 1]
                        d += relativedelta(
                            day=reset_day, hour=23, minute=59, second=59)
                    else:
                        d += relativedelta(months=diff_month, day=reset_day,
                                           hour=0, minute=0, second=0)
                    return True, d
            return False, d

        def proc_day_of_month(d):
            if expanded[2][0] != '*':
                days = DAYS[month - 1]
                if month == 2 and self.is_leap(year) is True:
                    days += 1
                if 'l' in expanded[2] and days==d.day:
                    return False, d

                if is_prev:
                    days_in_prev_month = DAYS[
                        (month - 2) % self.MONTHS_IN_YEAR]
                    diff_day = nearest_diff_method(
                        d.day, expanded[2], days_in_prev_month)
                else:
                    diff_day = nearest_diff_method(d.day, expanded[2], days)

                if diff_day is not None and diff_day != 0:
                    if is_prev:
                        d += relativedelta(
                            days=diff_day, hour=23, minute=59, second=59)
                    else:
                        d += relativedelta(
                            days=diff_day, hour=0, minute=0, second=0)
                    return True, d
            return False, d

        def proc_day_of_week(d):
            if expanded[4][0] != '*':
                diff_day_of_week = nearest_diff_method(
                    d.isoweekday() % 7, expanded[4], 7)
                if diff_day_of_week is not None and diff_day_of_week != 0:
                    if is_prev:
                        d += relativedelta(days=diff_day_of_week,
                                           hour=23, minute=59, second=59)
                    else:
                        d += relativedelta(days=diff_day_of_week,
                                           hour=0, minute=0, second=0)
                    return True, d
            return False, d

        def proc_hour(d):
            if expanded[1][0] != '*':
                diff_hour = nearest_diff_method(d.hour, expanded[1], 24)
                if diff_hour is not None and diff_hour != 0:
                    if is_prev:
                        d += relativedelta(
                            hours=diff_hour, minute=59, second=59)
                    else:
                        d += relativedelta(hours=diff_hour, minute=0, second=0)
                    return True, d
            return False, d

        def proc_minute(d):
            if expanded[0][0] != '*':
                diff_min = nearest_diff_method(d.minute, expanded[0], 60)
                if diff_min is not None and diff_min != 0:
                    if is_prev:
                        d += relativedelta(minutes=diff_min, second=59)
                    else:
                        d += relativedelta(minutes=diff_min, second=0)
                    return True, d
            return False, d

        def proc_second(d):
            if len(expanded) == 6:
                if expanded[5][0] != '*':
                    diff_sec = nearest_diff_method(d.second, expanded[5], 60)
                    if diff_sec is not None and diff_sec != 0:
                        d += relativedelta(seconds=diff_sec)
                        return True, d
            else:
                d += relativedelta(second=0)
            return False, d

        procs = [proc_month,
                 proc_day_of_month,
                 proc_day_of_week,
                 proc_hour,
                 proc_minute,
                 proc_second]

        while abs(year - current_year) <= 1:
            next = False
            for proc in procs:
                (changed, dst) = proc(dst)
                if changed:
                    day, month, year = dst.day, dst.month, dst.year
                    next = True
                    break
            if next:
                continue
            return self._datetime_to_timestamp(dst.replace(microsecond=0))

        if is_prev:
            raise CroniterBadDateError("failed to find prev date")
        raise CroniterBadDateError("failed to find next date")

    def _get_next_nearest(self, x, to_check):
        small = [item for item in to_check if item < x]
        large = [item for item in to_check if item >= x]
        large.extend(small)
        return large[0]

    def _get_prev_nearest(self, x, to_check):
        small = [item for item in to_check if item <= x]
        large = [item for item in to_check if item > x]
        small.reverse()
        large.reverse()
        small.extend(large)
        return small[0]

    def _get_next_nearest_diff(self, x, to_check, range_val):
        for i, d in enumerate(to_check):
            if d == "l":
                # if 'l' then it is the last day of month
                # => its value of range_val
                d = range_val
            if d >= x:
                return d - x
        return to_check[0] - x + range_val

    def _get_prev_nearest_diff(self, x, to_check, range_val):
        candidates = to_check[:]
        candidates.reverse()
        for d in candidates:
            if d != 'l' and d <= x:
                return d - x
        if 'l' in candidates:
            return -x
        candidate = candidates[0]
        for c in candidates:
            if c < range_val:
                candidate = c
                break

        return (candidate - x - range_val)

    def is_leap(self, year):
        if year % 400 == 0 or (year % 4 == 0 and year % 100 != 0):
            return True
        else:
            return False
