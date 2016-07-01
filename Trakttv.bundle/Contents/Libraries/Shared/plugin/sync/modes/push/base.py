from plugin.core.environment import Environment
from plugin.sync.core.enums import SyncMode
from plugin.sync.modes.core.base import Mode

import json
import os


class Base(Mode):
    mode = SyncMode.Push

    @classmethod
    def log_pending(cls, log, message, account, key, items):
        if type(items) is set:
            items = [
                (k, None)
                for k in items
            ]
        elif type(items) is dict:
            items = [
                (k, v)
                for k, v in items.items()
                if len(v) > 0
            ]
        else:
            raise ValueError('Unknown type for "pending" parameter')

        if len(items) < 1:
            return

        # Format items
        count, keys = cls.format_pending(items)

        # Update pending items report
        try:
            report_path = cls.write_pending(account, key, keys)
        except Exception, ex:
            log.warn('Unable to save report: %s', ex, exc_info=True)
            report_path = None

        # Display message in log file
        log.info(message, count, os.path.relpath(report_path, Environment.path.home))

    @classmethod
    def write_pending(cls, account, key, keys):
        directory = os.path.join(Environment.path.plugin_data, 'Reports', 'Sync', str(account.id), 'Pending')
        path = os.path.join(directory, '%s.json' % key)

        # Ensure directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Write items
        with open(path, 'w') as fp:
            json.dump(
                keys, fp,
                sort_keys=True,
                indent=4,
                separators=(',', ': ')
            )

        return path

    @classmethod
    def format_pending(cls, items):
        result = {}
        child_count = 0

        for key, children in items:
            key = '/'.join([str(k) for k in key])

            # Set show/movie
            result[key] = None

            if children is None:
                continue

            # Append keys of children
            result[key] = []

            for c_key in children:
                if type(c_key) is tuple and len(c_key) == 2:
                    c_key = 'S%02dE%02d' % c_key
                elif type(c_key) is tuple:
                    c_key = '/'.join([str(k) for k in c_key])

                result[key].append(c_key)
                child_count += 1

            # Sort children keys
            result[key] = sorted(result[key])

        if not child_count:
            return len(result), sorted(result.keys())

        return child_count, result
