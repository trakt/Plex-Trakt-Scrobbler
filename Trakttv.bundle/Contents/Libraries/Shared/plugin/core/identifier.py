from plugin.core.constants import GUID_SERVICES

from plex_metadata import Guid
import logging


log = logging.getLogger(__name__)


class Identifier(object):
    @classmethod
    def get_ids(cls, guids, strict=True):
        ids = {}

        if not guids:
            return ids

        for guid in guids:
            if type(guid.id) is str:
                # Parse raw guid
                guid = Guid.parse(guid.id, strict=strict)

            if guid and guid.valid and guid.service in GUID_SERVICES:
                ids[guid.service] = guid.id
            elif strict:
                return None

        return ids
