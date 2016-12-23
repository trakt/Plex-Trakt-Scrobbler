from plugin.core.backup.models.revision import BackupRevision
from plugin.core.helpers.variable import json_date_serializer

from datetime import datetime
import json
import logging

log = logging.getLogger(__name__)


class BackupArchive(BackupRevision):
    def __init__(self, date, archive, files, tag=None, attributes=None, path=None):
        if type(date) is not tuple:
            raise ValueError('Invalid value provided for "date" parameter')

        # Set attributes
        if attributes is None:
            attributes = {}

        attributes['date'] = date
        attributes['files'] = files

        # Construct revision
        super(BackupArchive, self).__init__(None, [archive], tag, attributes, path)

        # Set class properties
        self.files = files

        # Parse "date" tuple into a datetime object
        if len(date) == 2:
            self.timestamp = datetime(date[0], date[1], 1)
            self.period = 'month'
        elif len(date) == 1:
            self.timestamp = datetime(date[0], 1, 1)
            self.period = 'year'

    @property
    def date(self):
        if self.period == 'month':
            return self.timestamp.year, self.timestamp.month

        if self.period == 'year':
            return self.timestamp.year,

        raise ValueError('Invalid period: %r' % self.period)

    @classmethod
    def load(cls, path):
        # Read json from `path`
        with open(path, 'rb') as fp:
            metadata = json.load(fp)

        if not metadata:
            return None

        # Parse date
        date = metadata.pop('date')

        # Construct `BackupRevision` object
        return cls(
            date,
            metadata.pop('contents')[0],
            metadata.pop('files'),

            tag=metadata.pop('tag', None),
            attributes=metadata,
            path=path
        )

    def save(self, path):
        log.debug('Writing backup revision metadata to %r', path)

        try:
            # Write revision metadata to disk
            with open(path, 'wb') as fp:
                json.dump(self.dict(), fp, default=json_date_serializer)

        except Exception as ex:
            log.warn('Unable to save metadata - %s', ex, exc_info=True)
            return False

        # Update current revision path
        self.path = path

        return True

    def __repr__(self):
        properties = []

        if self.date:
            properties.append(('date', self.date))

        if self.path:
            properties.append(('path', self.path))

        return '<BackupArchive %s>' % (
            ', '.join([
                '%s: %r' % (key, value)
                for key, value in properties
            ])
        )
