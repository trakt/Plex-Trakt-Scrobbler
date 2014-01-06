from core.eventing import EventManager
from core.helpers import try_convert
from core.logger import Logger
from pts.activity import ActivityMethod, Activity
import websocket
import time

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


class WebSocket(ActivityMethod):
    name = 'WebSocket'

    opcode_data = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)

    def __init__(self):
        super(WebSocket, self).__init__()

        self.ws = None
        self.reconnects = 0

    def connect(self):
        self.ws = websocket.create_connection('ws://localhost:32400/:/websockets/notifications')
        
        log.info('Connected to notifications websocket')

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
            return

        try:
            info = JSON.ObjectFromString(data)
        except Exception, e:
            log.warn('Error decoding message from websocket: %s' % e)
            log.debug(data)
            return

        type = info.get('type')

        if not hasattr(self, 'process_%s' % type):
            log.debug('Unknown notification with type "%s"', type)
            log.debug('info: %s', info)
            return

        process_func = getattr(self, 'process_%s' % type)

        # Process each notification item
        for item in info['_children']:
            process_func(item)

    @staticmethod
    def process_playing(item):
        session_key = str(item['sessionKey'])
        state = str(item['state'])
        view_offset = try_convert(item['viewOffset'], int)

        EventManager.fire('notifications.playing', session_key, state, view_offset)

    @staticmethod
    def process_timeline(item):
        state_key = TIMELINE_STATES.get(item['state'])
        if state_key is None:
            log.warn('Unknown timeline state "%s"', item['state'])
            return

        EventManager.fire('notifications.timeline.%s' % state_key, item)

Activity.register(WebSocket, weight=None)
