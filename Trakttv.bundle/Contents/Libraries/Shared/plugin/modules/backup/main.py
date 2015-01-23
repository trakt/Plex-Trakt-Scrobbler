from plugin.core.environment import Environment
from plugin.modules.base import Module
from plugin.modules.backup.exceptions import PatchException
from plugin.modules.backup.packer import Packer
from plugin.modules.backup.revision import Revision

from datetime import datetime
import logging
import os

MAX_DELTA_CHAIN = 50
MIN_DELTA_SAVINGS = 0.25

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

        # Run backup for each flag separately
        timestamp = datetime.now()

        for flag in ['c', 'r', 'w']:
            br.run(store, flag, timestamp)

        return True


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
                revision = Revision.parse(self, directory, filename)

                if not revision:
                    continue

                result.append(revision)

        # Sort backup history
        self.history = sorted(result, key=lambda x: x.timestamp, reverse=True)

    def latest(self, include=None):
        """Retrieve latest revision

        :rtype: Revision or None
        """

        if not len(self.history):
            return None

        for revision in self.history:
            # Return a revision which matches our current `include` parameter
            if revision.include == include:
                return revision

        return None

    def run(self, store, include=None, timestamp=None):
        """Run backup task (create new revision if there are any changes)"""

        if include and type(include) is not list:
            include = [include]

        # Pack current library (for comparing with other revisions)
        current = self.pack(store, include)

        # Load latest version
        latest = self.latest(include)

        if not latest:
            log.debug("First run, creating a full revision...")
            return self.store('full', current, include, timestamp)

        # Compose diff
        latest_patch = latest.patch()

        # Ensure patch was successful
        if not latest_patch:
            log.debug('Patching failed, creating a full revision...')
            return self.store('full', current, include, timestamp)

        # Ensure our chain of deltas is less than 20 (to ensure patching is fast)
        if latest_patch.num_deltas > MAX_DELTA_CHAIN:
            log.debug('Reached deltas limit, creating a full revision...')
            return self.store('full', current, include, timestamp)

        # Compare latest revision against current library
        log.debug('Comparing current library against latest revision...')
        delta = self.diff(latest_patch.data, current)

        if not delta:
            log.debug("No changes detected")
            return True

        # Only store a delta if we reduce the item count by at least 25%
        if self.delta_savings(current, delta) < MIN_DELTA_SAVINGS:
            # Minimal revision delta savings, store full library
            log.debug("Minimal delta savings, creating a full revision...")
            return self.store('full', current, include, timestamp)

        log.debug('Creating a delta revision...')
        return self.store('delta', delta, include, timestamp)

    def store(self, type, data, include=None, timestamp=None):
        """Create `type` revision and write `data` to disk"""

        # Create revision
        rev = Revision.create(self, type, include, timestamp)

        # Save data for revision
        return rev.write(data.items())

    @staticmethod
    def delta_savings(current, delta):
        current_size = len(current)

        if not current_size:
            return 0

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
    def pack(store, include):
        result = {}

        for (agent, sid), value in store.items():
            # Replace with agent code
            agent = Packer.to_agent_code(agent)

            # Pack item into dictionary
            result[(agent, sid)] = Packer.pack(value, include)

        return result

    @staticmethod
    def patch(base, delta):
        # Added
        for key, value in delta.get('a', {}).items():
            if key in base:
                raise PatchException('Delta lists %r as added, but the item already exists' % (key, ))

            base[key] = value

        # Changed
        for key, value in delta.get('c', {}).items():
            if key not in base:
                raise PatchException('Delta lists %r as changed, but the item doesn\'t exist' % (key, ))

            base[key] = value

        # Removed
        for key in delta.get('r', []):
            if key not in base:
                raise PatchException('Delta lists %r as removed, but the item doesn\'t exist' % (key, ))

            del base[key]

        return base
