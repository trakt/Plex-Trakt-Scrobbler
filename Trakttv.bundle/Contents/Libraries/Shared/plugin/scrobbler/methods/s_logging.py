import logging

from plugin.scrobbler.methods.core.base import Base
from plugin.managers.session import SessionManager
from plex_activity import Activity


log = logging.getLogger(__name__)


class Logging(Base):
    def __init__(self):
        Activity.on('logging.playing', self.on_playing)

    def on_playing(self, info):
        log.debug('on_playing(%r)', info)

        session = SessionManager.from_logging(info)
