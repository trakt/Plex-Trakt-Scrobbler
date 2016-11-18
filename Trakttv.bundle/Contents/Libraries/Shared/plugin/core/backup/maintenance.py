from plugin.core.backup.constants import BACKUP_NAME_REGEX, BACKUP_PATH, BACKUP_PERIODS, BACKUP_RETENTION
from plugin.core.backup.models import BackupGroup, BackupRevision
from plugin.core.backup.tasks import ArchiveTask, CompactTask
from plugin.core.helpers.variable import try_convert

from datetime import datetime
from fnmatch import fnmatch
import logging
import os

log = logging.getLogger(__name__)


class BackupMaintenanceManager(object):
    def __init__(self):
        self.now = datetime.now()

    def run(self):
        # Run maintenance on backup groups
        for group in BackupGroup.list(max_depth=1):
            self.process_group(group)

    #
    # Process methods
    #

    def process_group(self, group):
        log.debug('Running maintenance on group: %r', group)

        # Process policy periods
        for period in BACKUP_PERIODS:
            self.process_period(period, group)

    def process_period(self, period, group):
        policy = BACKUP_RETENTION[period]

        # Retrieve options
        p_files = policy.get('files')

        if p_files is None:
            raise ValueError('Policy "%s" is missing the "files" attribute')

        # Build lists of revisions, grouped by period
        revisions_grouped = {}

        for base_path, dirs, files in os.walk(group.path):
            # Strip UNC prefix from `base_path`
            if base_path.startswith('\\\\?\\'):
                base_path = base_path[4:]

            # Ensure directory starts with a year
            rel_path = os.path.relpath(base_path, group.path)

            try:
                year = rel_path[:rel_path.index(os.path.sep)]
            except ValueError:
                year = rel_path

            if len(year) != 4 or try_convert(year, int) is None:
                continue

            # Search for revision metadata files
            for name in files:
                # Ensure file name matches the policy "files" filter
                if not fnmatch(name, p_files):
                    continue

                # Build path
                path = os.path.join(base_path, name)

                # Match revision metadata against regex pattern
                if not BACKUP_NAME_REGEX.match(name):
                    continue

                # Load metadata from file
                try:
                    revision = BackupRevision.load(path)
                except Exception as ex:
                    log.warn('Unable to load revision at %r: %s', path, ex, exc_info=True)
                    continue

                # Retrieve timestamp period
                key = self.timestamp_period(period, revision.timestamp)

                if key == self.timestamp_period(period, self.now):
                    # Backup occurred in the current period
                    continue

                # Store details in `revisions_grouped` dictionary
                if key not in revisions_grouped:
                    revisions_grouped[key] = []

                revisions_grouped[key].append(revision)

        # Ensure revisions have been found
        if not revisions_grouped:
            return

        log.debug('Processing period: %r (group: %r)', period, group)

        # Search for weeks exceeding the policy
        for key, revisions in revisions_grouped.items():
            # Compact period
            if policy.get('compact'):
                CompactTask.run(period, key, revisions, policy['compact'])

            # Archive revisions (if enabled)
            if policy.get('archive'):
                ArchiveTask.run(group, period, key, revisions, policy['archive'])

        log.debug('Done')

    #
    # Helpers
    #

    @staticmethod
    def timestamp_period(period, timestamp):
        if period == 'day':
            return timestamp.date()

        if period == 'week':
            return tuple(timestamp.isocalendar()[:2])

        if period == 'month':
            return timestamp.year, timestamp.month

        if period == 'year':
            return timestamp.year,

        raise ValueError('Unknown period: %r' % period)
