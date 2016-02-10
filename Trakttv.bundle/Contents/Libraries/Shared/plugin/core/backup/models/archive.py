from plugin.core.helpers.variable import json_date_serializer

from datetime import datetime
import json
import logging
import os

log = logging.getLogger(__name__)


class BackupArchive(object):
    def __init__(self, date, contents, attributes=None, path=None):
        self.date = date
        self.contents = contents

        self.attributes = attributes or {}

        self.path = path

    def dict(self):
        # Construct dictionary of data
        result = {
            'date': self.date,
            'contents': self.contents,
        }

        # Merge attributes
        result.update(self.attributes)

        return result

    @classmethod
    def load(cls, path):
        # Read json from `path`
        with open(path, 'rb') as fp:
            metadata = json.load(fp)

        if not metadata:
            return None

        # Parse date
        date = metadata.pop('date')

        if date:
            date = datetime.strptime(date, '%Y-%m-%d')

        # Construct `BackupRevision` object
        return cls(
            date,
            metadata.pop('contents'),

            attributes=metadata,
            path=path
        )

    def save(self, path):
        log.debug('Writing backup revision metadata to %r', path)

        try:
            # Write revision metadata to disk
            with open(path, 'wb') as fp:
                json.dump(self.dict(), fp, default=json_date_serializer)

        except Exception, ex:
            log.warn('Unable to save metadata - %s', ex, exc_info=True)
            return False

        # Update current revision path
        self.path = path

        return True

    def __repr__(self):
        properties = []

        if self.date:
            properties.append(('date', self.date.isoformat()))

        if self.path:
            properties.append(('path', self.path))

        return '<BackupArchive %s>' % (
            ', '.join([
                '%s: %r' % (key, value)
                for key, value in properties
            ])
        )
