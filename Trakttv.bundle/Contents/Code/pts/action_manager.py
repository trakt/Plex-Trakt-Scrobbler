from core.logger import Logger

from plex_activity import Activity

log = Logger('pts.action_manager')


class ActionManager(object):
    @classmethod
    def initialize(cls):
        Activity.on('logging.action.played', cls.on_played)\
                .on('logging.action.unplayed', cls.on_unplayed)

    @classmethod
    def on_played(cls, info):
        log.debug('on_played - %s', info)

    @classmethod
    def on_unplayed(cls, info):
        log.debug('on_unplayed - %s', info)
