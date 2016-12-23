from plugin.core.helpers.variable import json_date_serializer

from datetime import datetime
import json
import logging
import os

log = logging.getLogger(__name__)


class BackupRevision(object):
    def __init__(self, timestamp, contents, tag=None, attributes=None, path=None):
        self.timestamp = timestamp
        self.contents = contents

        self.tag = tag
        self.attributes = attributes or {}

        self.path = path

    def delete(self):
        if not self.path:
            log.warn('Revision has no "path" defined, unable to delete revision')
            return False

        log.info('Deleting revision: %r', self)

        # Delete revision metadata
        try:
            os.remove(self.path)
        except Exception as ex:
            log.warn('Unable to delete revision metadata file: %r - %s', self.path, ex, exc_info=True)
            return False

        # Delete revision contents
        directory = os.path.dirname(self.path)

        for name in self.contents:
            path = os.path.join(directory, name)

            if not os.path.exists(path):
                continue

            try:
                os.remove(path)
            except Exception as ex:
                log.warn('Unable to delete revision file: %r - %s', path, ex, exc_info=True)
                return False

        return True

    def dict(self):
        # Construct dictionary of data
        result = {
            'timestamp': self.timestamp,
            'contents': self.contents,
        }

        # Add revision "tag"
        if self.tag:
            result['tag'] = self.tag

        # Merge attributes
        result.update(self.attributes)

        return result

    @classmethod
    def load(cls, path):
        # Read json from `path`
        with open(path, 'rb') as fp:
            metadata = json.load(fp)

        if not metadata:
            raise ValueError('Invalid revision metadata: %r' % metadata)

        # Parse timestamp
        timestamp = metadata.pop('timestamp')

        if timestamp:
            timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')

        # Construct `BackupRevision` object
        return cls(
            timestamp,
            metadata.pop('contents'),

            tag=metadata.pop('tag', None),
            attributes=metadata,
            path=path
        )

    def save(self, path):
        log.debug('Writing backup revision metadata to %r', path)

        # Write revision metadata to disk
        with open(path, 'wb') as fp:
            json.dump(self.dict(), fp, default=json_date_serializer)

        # Update current revision path
        self.path = path

    def __repr__(self):
        properties = []

        if self.timestamp:
            properties.append(('timestamp', self.timestamp.isoformat()))

        if self.tag:
            properties.append(('tag', self.tag))

        if self.path:
            properties.append(('path', self.path))

        return '<BackupRevision %s>' % (
            ', '.join([
                '%s: %r' % (key, value)
                for key, value in properties
            ])
        )
