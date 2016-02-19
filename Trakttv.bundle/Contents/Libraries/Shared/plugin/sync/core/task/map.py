from plugin.core.constants import GUID_SERVICES

import logging

log = logging.getLogger(__name__)


class SyncMap(object):
    def __init__(self, task):
        self.task = task

        self._by_guid = {}
        self._by_key = {}

    def add(self, p_section_key, p_key, guids):
        if not guids or not p_key:
            return False

        for guid in guids:
            self.add_one(p_section_key, p_key, guid)

    def add_one(self, p_section_key, p_key, guid):
        if guid is None or p_key is None:
            return False

        p_key = int(p_key)

        # Flatten `guid`
        if type(guid) is not tuple:
            guid = (guid.service, guid.id)

        if guid[0] not in GUID_SERVICES:
            log.info('Unknown primary agent: %r -> %r (section: %r)', guid[0], p_key, p_section_key)

        # Store in `_by_guid` map
        if guid not in self._by_guid:
            self._by_guid[guid] = set()

        self._by_guid[guid].add((p_section_key, p_key))

        # Store in `_by_key` map
        if p_key not in self._by_key:
            self._by_key[p_key] = set()

        self._by_key[p_key].add(guid)

        return True

    def by_guid(self, guid):
        # Flatten `guid`
        if type(guid) is not tuple:
            guid = (guid.service, guid.id)

        return self._by_guid.get(guid, set())

    def by_key(self, rating_key):
        if rating_key is None:
            return set()

        return self._by_key.get(int(rating_key), set())
