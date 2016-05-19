from oem_framework.models.core import Model

import logging

log = logging.getLogger(__name__)


class Database(Model):
    def __init__(self, storage, source, target):
        self.storage = storage

        self.source = source
        self.target = target

        self.collections = {}

    def __repr__(self):
        return '<Database oem-%s-%s (%r)>' % (
            self.source,
            self.target,
            self.storage
        )
