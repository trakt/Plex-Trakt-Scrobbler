import logging

from plugin.scrobbler.methods.core.base import Base
from plugin.managers.session import WSessionManager
from plex_activity import Activity


log = logging.getLogger(__name__)


class Logging(Base):
    def __init__(self):
        Activity.on('logging.playing', self.on_playing)

    def on_playing(self, info):
        log.debug('on_playing(%r)', info)

        session = WSessionManager.from_logging(info)
