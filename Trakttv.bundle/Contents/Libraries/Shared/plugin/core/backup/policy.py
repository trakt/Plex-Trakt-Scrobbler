from plugin.core.backup.constants import BACKUP_NAME_REGEX, BACKUP_PATH, BACKUP_RETENTION
from plugin.core.backup.core.backup import Backup
from plugin.core.helpers.variable import try_convert

from datetime import datetime, date, timedelta
import json
import logging
import os

log = logging.getLogger(__name__)


class BackupPolicyMaintenance(object):
    def __init__(self):
        self.now = datetime.now()

    def run(self):
        # Run maintenance on backup groups
        for group in self.iter_groups(max_depth=1):
            self.process_group(group)

    #
    # Process methods
    #

    def process_group(self, group):
        log.debug('Running maintenance on group (group: %r)', group)

        # Process policy periods
        self.process_days(group)
        # self.process_weeks(group)
        # self.process_months(group)
        # self.process_years(group)

    def process_days(self, group):
        policy = BACKUP_RETENTION['day']

        action = policy.get('action')
        count = policy.get('count')

        if not count:
            raise Exception('Policy for "day" is missing the "count" attribute')

        # Build lists of backups, grouped by day
        backups = {}

        for base_path, dirs, files in os.walk(group):
            # Search for backup metadata files
            for name in files:
                # Ignore files without the ".bme" extension
                if not name.endswith('.bme'):
                    continue

                # Build path
                path = os.path.join(base_path, name)

                # Match backup metadata against regex pattern
                if not BACKUP_NAME_REGEX.match(name):
                    continue

                # Load metadata from file
                try:
                    backup = Backup.load(path)
                except Exception, ex:
                    log.warn('Unable to load backup metadata at %r: %s', path, ex, exc_info=True)
                    continue

                day = backup.timestamp.date()

                # Ignore backups that have occurred today
                if day == self.now.date():
                    continue

                # Store details in `backups` dictionary
                if day not in backups:
                    backups[day] = []

                backups[day].append(backup)

        # Search for days exceeding the policy
        for day, backups in backups.items():
            if len(backups) < count:
                continue

            # Compact day
            self.compact_day(day, backups, count)

        log.debug('Done')

    def process_weeks(self):
        pass

    def process_months(self):
        pass

    def process_years(self, group):
        policy = BACKUP_RETENTION['year']

        action = policy.get('action')
        count = policy.get('count')

        if not count:
            raise Exception('Policy for "year" is missing the "count" attribute')

        # Search for years that require actions
        for name in os.listdir(group):
            path = os.path.join(group, name)

            # Ensure `name` is a directory
            if not os.path.isdir(path):
                continue

            # Convert `name` to an integer (and skip invalid names)
            year = try_convert(name, int)

            if year is None:
                log.info('Invalid directory name %r, expecting an integer', name)
                continue

            # Ignore backups that have occurred this year
            if year == self.now.year:
                continue

            log.debug('Processing year: %r', path)

            # Compact year
            self.compact(path, count)

            # Archive year (if enabled)
            if action == 'archive':
                self.archive(path)

    #
    # Tasks
    #

    def archive(self, path):
        log.info('TODO archive() -  path: %r', path)

    def compact(self, path, count):
        log.info('TODO compact() - path: %r, count: %r', path, count)

    def compact_day(self, day, backups, maximum):
        log.info('Compacting day: %r - len(backups): %r, maximum: %r', day, len(backups), maximum)

        # Sort backups by timestamp
        backups = sorted(backups, key=lambda b: b.timestamp)

        # Build list of backups, sorted by time to closest backup
        closest_backups = []

        for x in xrange(len(backups)):
            if x + 1 >= len(backups):
                continue

            left = backups[x]
            right = backups[x + 1]

            # Calculate time between `left` and `right`
            span = right.timestamp - left.timestamp

            # Append item to list
            closest_backups.append((span.total_seconds(), left, right))

        # Remove closest backups (by timestamp) until maximum count is reached
        closest_backups = sorted(closest_backups, key=lambda item: item[0])

        for x in xrange(len(backups) - maximum):
            distance, _, backup = closest_backups[x]

            log.info('Removing backup: %r', backup)

    #
    # Helpers
    #

    def iter_groups(self, search_path=BACKUP_PATH, max_depth=0):
        names = os.listdir(search_path)

        for name in names:
            path = os.path.join(search_path, name)

            if path.endswith('.bgr'):
                # Backup group found
                yield path
            elif max_depth > 0:
                # Search sub-directory for backup groups
                for p in self.iter_groups(path, max_depth - 1):
                    yield p
