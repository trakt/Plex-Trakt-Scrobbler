from core.helpers import total_seconds
from core.logger import Logger
from data.watch_session import WatchSession
from pts.scrobbler import ScrobblerMethod

from datetime import datetime
from threading import Thread
import traceback
import time

log = Logger('pts.session_manager')


class SessionManager(Thread):
    def __init__(self):
        self.active = True

        super(SessionManager, self).__init__()

    def run(self):
        while self.active:
            try:
                self.check_sessions()
            except Exception, ex:
                log.error('Exception raised in session manager: %s', ex, exc_info=True)

            time.sleep(5)

    def check_sessions(self):
        sessions = WatchSession.all()

        if not len(sessions):
            return

        for key, ws in sessions:
            if getattr(ws, 'skip', True):
                continue

            try:
                self.check_paused(ws)
            except AttributeError, ex:
                log.warn("Unable to determine if session is paused, skipping invalid session - %s", ex, exc_info=True)
                ws.skip = True

    def check_paused(self, ws):
        if not ws or ws.cur_state != 'paused' or not ws.paused_since:
            return

        if ws.active and Datetime.Now() > ws.paused_since + Datetime.Delta(seconds=15):
            log.debug("%s paused for 15s, watching status cancelled" % ws.title)
            ws.active = False
            ws.save()

            if not self.send_action(ws, 'pause'):
                log.info('Failed to send "pause" action for watch session')

    def start(self):
        # Cleanup sessions
        self.cleanup()

        # Start thread
        super(SessionManager, self).start()

    def stop(self):
        self.active = False

    @staticmethod
    def send_action(ws, action):
        if not ws.type:
            return False

        if ScrobblerMethod.handle_action(ws, action):
            return False

        return True

    @staticmethod
    def cleanup():
        log.debug('Cleaning up stale or invalid sessions')

        sessions = WatchSession.all()

        if not len(sessions):
            return

        for key, ws in sessions:
            delete = False

            # Destroy invalid sessions
            if ws is None:
                delete = True
            elif not ws.last_updated or type(ws.last_updated) is not datetime:
                delete = True
            elif total_seconds(datetime.now() - ws.last_updated) / 60 / 60 > 24:
                # Destroy sessions last updated over 24 hours ago
                log.debug('Session %s was last updated over 24 hours ago, queued for deletion', key)
                delete = True

            # Delete session or flag for update
            if delete:
                log.info('Session %s looks stale or invalid, deleting it now', key)
                WatchSession.delete(key)
            elif not ws.update_required:
                log.info('Queueing session %s for update', key)
                ws.update_required = True
                ws.save()

        log.debug('Finished cleaning up')
