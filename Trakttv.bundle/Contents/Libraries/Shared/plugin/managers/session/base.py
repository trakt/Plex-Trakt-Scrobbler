from plugin.core.constants import GUID_SERVICES
from plugin.managers.core.base import Get, Update
from plugin.modules.core.manager import ModuleManager
from plugin.scrobbler.core.session_prefix import SessionPrefix

from oem.media.show import EpisodeIdentifier, EpisodeMatch
from plex_metadata import Metadata, Guid
import logging
import math

log = logging.getLogger(__name__)


class Base(object):
    @classmethod
    def build_session_key(cls, session_key):
        if type(session_key) is str:
            return session_key

        # Prepend session prefix
        session_prefix = SessionPrefix.get()

        return '%s:%s' % (
            session_prefix,
            session_key
        )


class GetSession(Get, Base):
    pass


class UpdateSession(Update, Base):
    @staticmethod
    def get_account(result):
        # Try retrieve account from client
        client = result.get('client')

        try:
            client_account_id = client.account_id if client else None
        except KeyError:
            client_account_id = None

        if client_account_id:
            # Valid account found
            return client_account_id

        # Try retrieve account from user
        user = result.get('user')

        try:
            user_account_id = user.account_id if user else None
        except KeyError:
            user_account_id = None

        if user_account_id:
            # Valid account found
            return user_account_id

        return None

    @staticmethod
    def get_metadata(rating_key):
        # Retrieve metadata for `rating_key`
        try:
            metadata = Metadata.get(rating_key)
        except NotImplementedError as ex:
            log.debug('%r, ignoring session', ex.message)
            return None, None

        # Ensure metadata was returned
        if not metadata:
            return None, None

        # Validate metadata
        if metadata.type not in ['movie', 'episode']:
            log.info('Ignoring metadata with type %r for rating_key %r', metadata.type, rating_key)
            return metadata, None

        # Parse guid
        guid = Guid.parse(metadata.guid, strict=True)

        return metadata, guid

    @classmethod
    def match_parts(cls, p_metadata, guid, view_offset):
        if p_metadata.type != 'episode':
            # TODO support multi-part movies
            return 1, 1, p_metadata.duration

        # Retrieve number of parts
        if guid.service in GUID_SERVICES:
            # Parse parts from filename
            _, episodes = ModuleManager['matcher'].process(p_metadata)

            part_count = len(episodes)
        else:
            season_num = p_metadata.season.index
            episode_num = p_metadata.index

            # Process guid episode identifier overrides
            if guid.season is not None:
                season_num = guid.season

            # Retrieve episode mappings from OEM
            supported, match = ModuleManager['mapper'].map(
                guid.service, guid.id,
                EpisodeIdentifier(season_num, episode_num),
                resolve_mappings=False
            )

            if not supported or not match:
                return 1, 1, p_metadata.duration

            if not isinstance(match, EpisodeMatch):
                log.info('Movie mappings are not supported')
                return 1, 1, p_metadata.duration

            part_count = len(match.mappings) or 1

        # Determine the current part number
        part, part_duration = cls.get_part(
            p_metadata.duration,
            view_offset,
            part_count
        )

        return part, part_count, part_duration

    @staticmethod
    def get_part(duration, view_offset, part_count):
        if duration is None or part_count is None or part_count < 1:
            return 1, duration

        part_duration = int(math.floor(
            float(duration) / part_count
        ))

        # Calculate current part number
        part = int(math.floor(
            float(view_offset) / part_duration
        )) + 1

        # Clamp `part` to: 0 - `total_parts`
        return max(0, min(part, part_count)), part_duration

    @staticmethod
    def get_progress(duration, view_offset, part=1, part_count=1, part_duration=None):
        if duration is None:
            return None

        if part_count > 1 and part_duration is not None:
            # Update attributes for part progress calculations
            duration = part_duration
            view_offset -= (part_duration * (part - 1))

        # Calculate progress (0 - 100)
        return round((float(view_offset) / duration) * 100, 2)
