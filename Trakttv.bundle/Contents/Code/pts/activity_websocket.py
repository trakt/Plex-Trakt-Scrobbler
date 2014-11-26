from core.eventing import EventManager
from core.helpers import try_convert, all
from core.logger import Logger
from pts.activity import ActivityMethod, Activity

from urllib import urlencode
import os
import time
import websocket

log = Logger('pts.activity_websocket')


TIMELINE_STATES = {
    0: 'created',
    2: 'matching',
    3: 'downloading',
    4: 'loading',
    5: 'finished',
    6: 'analyzing',
    9: 'deleted'
}

REGEX_STATUS_SCANNING = Regex('Scanning the "(?P<section>.*?)" section')
REGEX_STATUS_SCAN_COMPLETE = Regex('Library scan complete')


class WebSocketActivity(ActivityMethod):
    name = 'WebSocketActivity'

    opcode_data = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)

    def __init__(self):
        super(WebSocketActivity, self).__init__()

        self.ws = None
        self.reconnects = 0

    def connect(self):
        uri = 'ws://127.0.0.1:32400/:/websockets/notifications'
        params = {}

        # Set authentication token (if one is available)
        if os.environ.get('PLEXTOKEN'):
            params['X-Plex-Token'] = os.environ['PLEXTOKEN']
        else:
            log.warn('Invalid token (X-Plex-Token: %r), unable to send authentication parameter', os.environ.get('PLEXTOKEN'))

        # Append parameters to uri
        if params:
            uri += '?' + urlencode(params)

        # Create websocket connection
        self.ws = websocket.create_connection(uri)

    def run(self):
        self.connect()

        log.debug('Ready')

        while True:
            try:
                self.process(*self.receive())

                # successfully received data, reset reconnects counter
                self.reconnects = 0

            except websocket.WebSocketConnectionClosedException:
                if self.reconnects <= 5:
                    self.reconnects = self.reconnects + 1

                    # Increasing sleep interval between reconnections
                    if self.reconnects > 1:
                        time.sleep(2 * (self.reconnects - 1))

                    log.info('WebSocket connection has closed, reconnecting...')
                    self.connect()
                else:
                    log.error('WebSocket connection unavailable, activity monitoring not available')
                    break

    def receive(self):
        frame = self.ws.recv_frame()

        if not frame:
            raise websocket.WebSocketException("Not a valid frame %s" % frame)
        elif frame.opcode in self.opcode_data:
            return frame.opcode, frame.data
        elif frame.opcode == websocket.ABNF.OPCODE_CLOSE:
            self.ws.send_close()
            return frame.opcode, None
        elif frame.opcode == websocket.ABNF.OPCODE_PING:
            self.ws.pong("Hi!")

        return None, None

    def process(self, opcode, data):
        if opcode not in self.opcode_data:
            return False

        try:
            info = JSON.ObjectFromString(data)
        except Exception, e:
            log.warn('Error decoding message from websocket: %s' % e)
            log.debug(data)
            return False

        type = info.get('type')
        process_func = getattr(self, 'process_%s' % type, None)

        # Process each notification item
        if process_func:
            results = [process_func(item) for item in info['_children']]

            if len(results) and results[0]:
                return True

        log.debug('Unable to process notification: %s', info)
        return False

    @staticmethod
    def process_playing(item):
        session_key = item.get('sessionKey')
        state = item.get('state')
        view_offset = try_convert(item.get('viewOffset'), int)

        valid = all([
            x is not None
            for x in [session_key, state, view_offset]
        ])

        if valid:
            EventManager.fire('notifications.playing', str(session_key), str(state), view_offset)
            return True

        log.warn("'playing' notification doesn't look valid, ignoring: %s" % item)
        return False

    @staticmethod
    def process_timeline(item):
        state_key = TIMELINE_STATES.get(item['state'])
        if state_key is None:
            log.warn('Unknown timeline state "%s"', item['state'])
            return False

        EventManager.fire('notifications.timeline.%s' % state_key, item)
        return True

    @staticmethod
    def process_progress(item):
        # Not using this yet, this suppresses the 'Unable to process...' messages for now though
        return True

    @staticmethod
    def process_status(item):
        if item.get('notificationName') != 'LIBRARY_UPDATE':
            log.debug('Unknown notification name "%s"', item.get('notificationName'))
            return False

        title = item.get('title')

        # Check for scan complete message
        if REGEX_STATUS_SCAN_COMPLETE.match(title):
            EventManager.fire('notifications.status.scan_complete')
            return True

        # Check for scanning message
        match = REGEX_STATUS_SCANNING.match(title)
        if match:
            section = match.group('section')

            if section:
                EventManager.fire('notifications.status.scanning', section)
                return True

        log.debug('No matches found for %s', item)
        return False

Activity.register(WebSocketActivity, weight=None)
