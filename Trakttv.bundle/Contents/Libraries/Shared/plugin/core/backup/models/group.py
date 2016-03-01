from plugin.core.backup.constants import BACKUP_PATH

import os


class BackupGroup(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path

    @classmethod
    def load(cls, path):
        name = os.path.relpath(path, BACKUP_PATH)

        return cls(name, path)

    @classmethod
    def list(cls, search_path=BACKUP_PATH, max_depth=0):
        if not os.path.isdir(search_path):
            return

        names = os.listdir(search_path)

        for name in names:
            path = os.path.join(search_path, name)

            if path.endswith('.bgr'):
                # Load backup group
                yield cls.load(path)
            elif max_depth > 0 and os.path.isdir(path):
                # Search sub-directory for backup groups
                for p in cls.list(path, max_depth - 1):
                    yield p

    def __repr__(self):
        return '<BackupGroup name: %r>' % self.name
