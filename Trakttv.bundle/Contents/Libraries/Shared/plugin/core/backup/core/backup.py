from datetime import datetime
import json


class Backup(object):
    def __init__(self):
        self.timestamp = None
        self.contents = None

        self.tag = None
        self.attributes = {}

    @classmethod
    def load(cls, path):
        # Read json from `path`
        with open(path, 'rb') as fp:
            metadata = json.load(fp)

        if not metadata:
            return None

        # Construct `Backup` object
        backup = cls()

        # Parse timestamp
        timestamp = metadata.pop('timestamp')

        if timestamp:
            timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')

        # Set attributes
        backup.timestamp = timestamp
        backup.contents = metadata.pop('contents')

        backup.tag = metadata.pop('tag', None)
        backup.attributes = metadata

        return backup

    def __repr__(self):
        return '<Backup timestamp: %r, tag: %r>' % (
            self.timestamp,
            self.tag
        )
