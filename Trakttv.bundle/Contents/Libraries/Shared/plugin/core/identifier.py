from plugin.core.constants import GUID_SERVICES

from plex_metadata import Guid
import logging


log = logging.getLogger(__name__)


class Identifier(object):
    @classmethod
    def get_ids(cls, guid, strict=True):
        ids = {}

        if not guid:
            return ids

        if type(guid) is str:
            # Parse raw guid
            guid = Guid.parse(guid, strict=strict)

        if guid and guid.valid and guid.service in GUID_SERVICES:
            ids[guid.service] = guid.id
        elif strict:
            return None

        return ids
