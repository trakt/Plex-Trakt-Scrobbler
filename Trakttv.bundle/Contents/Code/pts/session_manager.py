from data.watch_session import WatchSession
from pts.scrobbler import ScrobblerMethod

from threading import Thread
import traceback
import time


class SessionManager(Thread):
    def __init__(self):
        self.active = True

        super(SessionManager, self).__init__()

    def run(self):
        while self.active:
            try:
                self.check_sessions()
            except Exception, ex:
                trace = traceback.format_exc()
                Log.Warn('Exception from SessionManager (%s): %s' % (ex, trace))

            time.sleep(5)

    def check_sessions(self):
        sessions = WatchSession.all()

        if not len(sessions):
            return

        for key, ws in sessions:
            self.check_paused(ws)

    def check_paused(self, ws):
        if ws.cur_state != 'paused' or not ws.paused_since:
            return

        if ws.watching and Datetime.Now() > ws.paused_since + Datetime.Delta(seconds=15):
            Log.Debug("%s paused for 15s, watching status cancelled" % ws.title)
            ws.watching = False
            ws.save()

            if not self.send_action(ws, 'cancelwatching'):
                Log.Info('Failed to cancel the watching status')

    def send_action(self, ws, action):
        if not ws.type:
            return False

        if ScrobblerMethod.handle_action(ws, ws.type, action, ws.cur_state):
            return False

        Dict.Save()
        return True

    def stop(self):
        self.active = False
