from collections import namedtuple
from datetime import datetime
import logging
import msgpack
import os

log = logging.getLogger(__name__)

PatchResult = namedtuple('PatchResult', ['data', 'num_deltas'])


class Revision(object):
    def __init__(self, manager, timestamp, type):
        self.manager = manager

        self.timestamp = timestamp
        self.type = type

    @property
    def directory(self):
        return os.path.join(
            self.manager.destination,
            self.timestamp.strftime('%y-%m')
        )

    @property
    def path(self):
        return os.path.join(
            self.directory,
            '%s.%s' % (self.timestamp.strftime('%d_%H-%M-%S'), self.type)
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
            if r.type == 'full':
                base = r
                break

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

            self.manager.patch(result, dict(r_data))

        return PatchResult(result, len(deltas))

    def get(self):
        """Resolve data for this revision (by applying deltas to a base)

        :rtype: dict
        """

        # Get patched result
        result = self.patch()

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
    def create(cls, manager, type, timestamp=None):
        """Create a new revision

        :rtype: Revision
        """

        if timestamp is None:
            timestamp = datetime.now()

        return cls(manager, timestamp, type)

    @classmethod
    def parse(cls, manager, directory, filename):
        """Parse revision from directory/filename

        :rtype: Revision
        """

        name, ext = os.path.splitext(filename)

        # Create timestamp from fragments
        timestamp = datetime.strptime('-'.join([directory, name]), '%y-%m-%d_%H-%M-%S')

        # Create `Revision` object
        return cls(manager, timestamp, ext.lstrip('.'))
