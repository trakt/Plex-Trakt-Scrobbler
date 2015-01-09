from plugin.modules.backup.exceptions import PatchException

from collections import namedtuple
from datetime import datetime
import logging
import msgpack
import os
import re

log = logging.getLogger(__name__)

RE_FILENAME = re.compile(r"(?P<timestamp>\d+_\d+-\d+-\d+)(_(?P<include>.*))?", re.IGNORECASE)

PatchResult = namedtuple('PatchResult', ['data', 'num_deltas'])


class Revision(object):
    def __init__(self, manager, type, include, timestamp):
        self.manager = manager

        self.type = type
        self.include = sorted(include) if include else None
        self.timestamp = timestamp

    @property
    def directory(self):
        return os.path.join(
            self.manager.destination,
            self.timestamp.strftime('%y-%m')
        )

    @property
    def path(self):
        name = self.timestamp.strftime('%d_%H-%M-%S')

        if self.include is not None:
            name += '_' + ''.join(self.include)

        return os.path.join(
            self.directory,
            '%s.%s' % (name, self.type)
        )

    def patch(self):
        """Resolve data for this revision (by patching deltas to a base)

        :rtype: PatchResult
        """

        # Find position of `self` in history
        pos = self.manager.history.index(self)

        # Look for base revision, store any intermediate deltas
        base = None
        deltas = []

        for r in self.manager.history[pos:]:
            # Skip revisions which don't match our current `include` parameter
            if r.include != self.include:
                continue

            # Finish when we find the closest "full" revision
            if r.type == 'full':
                base = r
                break

            # Store deltas for later patching
            if r.type == 'delta':
                deltas.append(r)

        if base is None:
            log.warn('Unable to find base revision')
            return None

        result = base.read()

        if result is None:
            log.warn('Unable to read base revision')
            return None

        result = dict(result)

        # Apply deltas (in reverse order)
        log.debug('Applying %d delta(s) to base revision...', len(deltas))

        for r in deltas[::-1]:
            r_data = r.read()

            if r_data is None:
                log.warn('Unable to read delta revision')
                return None

            try:
                self.manager.patch(result, dict(r_data))
            except PatchException, ex:
                log.warn('Unable to patch base revision with delta %r - %r', r.timestamp, ex)
                return None

        return PatchResult(result, len(deltas))

    def get(self):
        """Resolve data for this revision (by applying deltas to a base)

        :rtype: dict
        """

        # Get patched result
        result = self.patch()

        if result is None:
            return None

        # Return just the data
        return result.data

    def read(self):
        """Read raw revision from disk"""

        with open(self.path, 'rb') as fp:
            raw = fp.read()

        if not raw:
            return None

        try:
            return msgpack.unpackb(raw, use_list=False)
        except ValueError, ex:
            return None

    def write(self, data):
        """Write raw revision to disk"""

        # Ensure root folder exists
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

        # Encode to JSON string
        encoded = msgpack.packb(data)

        # Write to disk
        with open(self.path, 'wb') as fp:
            fp.write(encoded)

        return True

    @classmethod
    def create(cls, manager, type, include=None, timestamp=None):
        """Create a new revision

        :rtype: Revision
        """

        if timestamp is None:
            timestamp = datetime.now()

        return cls(manager, type, include, timestamp)

    @classmethod
    def parse(cls, manager, directory, filename):
        """Parse revision from directory/filename

        :rtype: Revision
        """

        name, ext = os.path.splitext(filename)

        match = RE_FILENAME.match(name)

        if match is None:
            return None

        # Create timestamp from fragments
        timestamp = datetime.strptime('-'.join([directory, match.group('timestamp')]), '%y-%m-%d_%H-%M-%S')

        # Get `include` parameter from match
        include = match.group('include')

        if include is not None:
            include = list(include)

        # Create `Revision` object
        return cls(manager, ext.lstrip('.'), include, timestamp)

    def __repr__(self):
        return '<Revision type: %r, include: %r, timestamp: %r>' % (
            self.type,
            self.include,
            self.timestamp
        )
