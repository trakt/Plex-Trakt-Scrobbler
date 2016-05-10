from oem_framework.core.helpers import median

import inspect
import sys
import time


class Elapsed(object):
    samples = {}

    @classmethod
    def calculate_sample_statistics(cls, raw_samples):
        if not raw_samples:
            return None

        minimum = None
        maximum = None
        total = 0

        actual_samples = []

        for value in raw_samples:
            if value <= 0:
                continue

            if minimum is None or value < minimum:
                minimum = value

            if maximum is None or value > maximum:
                maximum = value

            total += value

            actual_samples.append(value)

        if len(actual_samples) < 1:
            return None

        avg = total / len(actual_samples)
        med = median(actual_samples)

        return {
            'count_actual': len(actual_samples),
            'count_raw': len(raw_samples),

            'minimum': minimum,
            'maximum': maximum,
            'total': total,

            'average': avg,
            'median': med
        }

    @classmethod
    def calculate_statistics(cls):
        items = []

        # Calculate and display statistics for each function
        for f_name, groups in cls.samples.items():
            for result, samples in groups.items():
                statistics = cls.calculate_sample_statistics(samples)

                if not statistics:
                    continue

                items.append((f_name, result, statistics))

        # Sort by total elapsed time
        def sort_key((function_name, result, statistics)):
            return statistics['total']

        items.sort(key=sort_key, reverse=True)
        return items

    @classmethod
    def format_statistics(cls, line_format='%-46s %-10s %-16s %-16s %-16s %-16s %-16s %-16s'):
        # Display header
        yield line_format % ('Function', 'Result', 'Samples', 'Minimum (ms)', 'Maximum (ms)', 'Average (ms)', 'Median (ms)', 'Total (ms)')

        # Calculate and display statistics for each function
        for function_name, result, statistics in cls.calculate_statistics():
            yield line_format % (
                function_name, result,
                '%d/%d' % (
                    statistics['count_actual'],
                    statistics['count_raw']
                ),
                int(round(statistics['minimum'], 0)),
                int(round(statistics['maximum'], 0)),
                int(round(statistics['average'], 0)),
                int(round(statistics['median'], 0)),
                int(round(statistics['total'], 0))
            )

    @classmethod
    def track(cls, func):
        def wrapper(*args, **kwargs):
            # Retrieve function name
            f_name = func.__name__

            if args and args[0]:
                if inspect.isclass(args[0]):
                    f_name = args[0].__name__ + '.' + f_name
                elif hasattr(args[0], '__class__'):
                    f_name = args[0].__class__.__name__ + '.' + f_name

            # Clock call time
            started_at = time.time()
            failure = False

            try:
                return func(*args, **kwargs)
            except Exception:
                exc_info = sys.exc_info()
                failure = True

                raise exc_info[0], exc_info[1], exc_info[2]
            finally:
                elapsed = round((time.time() - started_at) * 1000, 4)

                if f_name not in cls.samples:
                    cls.samples[f_name] = {
                        'failure': [],
                        'success': []
                    }

                if failure:
                    cls.samples[f_name]['failure'].append(elapsed)
                else:
                    cls.samples[f_name]['success'].append(elapsed)

        return wrapper
