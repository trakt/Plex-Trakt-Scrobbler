from plugin.core.environment import Environment
from plugin.modules.base import Module
from plugin.modules.backup.packer import Packer
from plugin.modules.backup.revision import Revision

import logging
import os

log = logging.getLogger(__name__)


class Backup(Module):
    __key__ = 'backup'

    def __init__(self):
        self.destination = os.path.join(Environment.path.plugin_data, 'Backups')

    def run(self, group, store):
        destination = os.path.join(self.destination, group)

        # Ensure all the folders exist
        if not os.path.exists(destination):
            os.makedirs(destination)

        br = BackupRunner(destination)

        # Resolve revision history
        br.resolve()

        # Run backup
        return br.run(store)


class BackupRunner(object):
    def __init__(self, destination):
        self.destination = destination
        self.history = None

    def resolve(self):
        """Resolve revision history"""

        result = []

        for root, _, files in os.walk(self.destination):
            if root == self.destination:
                continue

            # Parse root directory name
            directory = os.path.basename(root)

            for filename in files:
                result.append(Revision.parse(self, directory, filename))

        # Sort backup history
        self.history = sorted(result, key=lambda x: x.timestamp, reverse=True)

    def latest(self):
        """Retrieve latest revision

        :rtype: Revision or None
        """

        if not len(self.history):
            return None

        return self.history[0]

    def run(self, store):
        """Run backup task (create new revision if there are any changes)"""

        # Pack current library (for comparing with other revisions)
        current = self.pack(store)

        # Load latest version
        latest = self.latest()

        if not latest:
            log.debug("First run, creating a full revision...")
            return self.store('full', current)

        # Compose diff
        latest_patch = latest.patch()

        # Ensure our chain of deltas is less than 20 (to ensure patching is fast)
        if latest_patch.num_deltas > 20:
            log.debug('Reached deltas limit, creating a full revision...')
            return self.store('full', current)

        # Compare latest revision against current library
        log.debug('Comparing current library against latest revision...')
        delta = self.diff(latest_patch.data, current)

        if not delta:
            log.debug("No changes detected")
            return True

        # Only store a delta if we reduce the item count by at least 25%
        if self.delta_savings(current, delta) < 0.25:
            # Minimal revision delta savings, store full library
            log.debug("Minimal delta savings, creating a full revision...")
            return self.store('full', current)

        log.debug('Creating a delta revision...')
        return self.store('delta', delta)

    def store(self, type, data):
        """Create `type` revision and write `data` to disk"""

        # Create revision
        rev = Revision.create(self, type)

        # Save data for revision
        return rev.write(data.items())

    @staticmethod
    def delta_savings(current, delta):
        current_size = len(current)
        delta_size = sum([len(x) for x in delta.values()])

        return 1 - (float(delta_size) / current_size)

    @staticmethod
    def diff(previous, current):
        s_previous = set(previous.keys())
        s_current = set(current.keys())

        s_intersect = s_current.intersection(s_previous)

        # Find items that have been added/removed
        added = s_current - s_intersect
        removed = s_previous - s_intersect

        # Find items that have changed
        changed = [
            key for key in s_intersect
            if previous[key]['@'] != current[key]['@']
        ]

        # Build delta structure
        result = {}

        if added:
            result['a'] = dict([(key, current[key]) for key in added])

        if changed:
            result['c'] = dict([(key, current[key]) for key in changed])

        if removed:
            result['r'] = [key for key in removed]

        return result

    @staticmethod
    def pack(store):
        result = {}

        for key, value in store.items():
            result[key] = Packer.pack(value)

        return result

    @staticmethod
    def patch(base, delta):
        # Added
        for key, value in delta.get('a', {}).items():
            base[key] = value

        # Changed
        for key, value in delta.get('c', {}).items():
            base[key] = value

        # Removed
        for key in delta.get('r', []):
            del base[key]

        return base
