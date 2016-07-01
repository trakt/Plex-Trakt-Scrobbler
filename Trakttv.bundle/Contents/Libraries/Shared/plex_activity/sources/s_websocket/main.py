from plex import Plex
from plex.lib.six.moves.urllib_parse import urlencode
from plex_activity.sources.base import Source

import json
import logging
import re
import time
import websocket

log = logging.getLogger(__name__)

SCANNING_REGEX = re.compile('Scanning the "(?P<section>.*?)" section', re.IGNORECASE)
SCAN_COMPLETE_REGEX = re.compile('Library scan complete', re.IGNORECASE)

TIMELINE_STATES = {
    0: 'created',
    2: 'matching',
    3: 'downloading',
    4: 'loading',
    5: 'finished',
    6: 'analyzing',
    9: 'deleted'
}


class WebSocket(Source):
    name = 'websocket'
    events = [
        'websocket.playing',

        'websocket.scanner.started',
        'websocket.scanner.progress',
        'websocket.scanner.finished',

        'websocket.timeline.created',
        'websocket.timeline.matching',
        'websocket.timeline.downloading',
        'websocket.timeline.loading',
        'websocket.timeline.finished',
        'websocket.timeline.analyzing',
        'websocket.timeline.deleted'
    ]

    opcode_data = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)

    def __init__(self, activity):
        super(WebSocket, self).__init__()

        self.ws = None
        self.reconnects = 0

        # Pipe events to the main activity instance
        self.pipe(self.events, activity)

    def connect(self):
        uri = 'ws://%s:%s/:/websockets/notifications' % (
            Plex.configuration.get('server.host', '127.0.0.1'),
            Plex.configuration.get('server.port', 32400)
        )

        params = {}

        # Set authentication token (if one is available)
        if Plex.configuration['authentication.token']:
            params['X-Plex-Token'] = Plex.configuration['authentication.token']

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
                    self.reconnects += 1

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
            info = json.loads(data)
        except UnicodeDecodeError as ex:
            log.warn('Error decoding message from websocket: %s' % ex, extra={
                'event': {
                    'module': __name__,
                    'name': 'process.loads.unicode_decode_error',
                    'key': '%s:%s' % (ex.encoding, ex.reason)
                }
            })
            log.debug(data)
            return False
        except Exception as ex:
            log.warn('Error decoding message from websocket: %s' % ex, extra={
                'event': {
                    'module': __name__,
                    'name': 'process.load_exception',
                    'key': ex.message
                }
            })
            log.debug(data)
            return False

        type = info.get('type')

        if not type:
            return False

        # Pre-process message (if function exists)
        process_func = getattr(self, 'process_%s' % type, None)

        if process_func and process_func(info):
            return True

        # Emit raw message
        self.emit_notification('%s.notification.%s' % (self.name, type), info)
        return True

    def process_playing(self, info):
        self.emit_notification('%s.playing' % self.name, info)
        return True

    def process_progress(self, info):
        if not info.get('_children'):
            return False

        notification = info['_children'][0]

        self.emit_notification('%s.scanner.progress' % self.name, {
            'message': notification.get('message')
        })
        return True

    def process_status(self, info):
        if not info.get('_children'):
            return False

        notification = info['_children'][0]

        title = notification.get('title')

        if not title:
            return False

        # Scan complete message
        if SCAN_COMPLETE_REGEX.match(title):
            self.emit_notification('%s.scanner.finished' % self.name)
            return True

        # Scanning message
        match = SCANNING_REGEX.match(title)

        if match:
            section = match.group('section')

            if section:
                self.emit_notification('%s.scanner.started' % self.name, {
                    'section': section
                })
                return True

        return False

    def process_timeline(self, info):
        children = info.get('_children', [])

        if not children:
            return False

        for entry in children:
            state = TIMELINE_STATES.get(entry.get('state'))

            if not state:
                continue

            self.emit('%s.timeline.%s' % (self.name, state), entry)

        return True

    def emit_notification(self, name, info=None):
        if info is None:
            info = {}

        children = info.get('_children', [])

        if len(children) > 1:
            self.emit(name, children)
        elif len(children) == 1:
            self.emit(name, children[0])
        elif info:
            self.emit(name, info)
        else:
            self.emit(name)
