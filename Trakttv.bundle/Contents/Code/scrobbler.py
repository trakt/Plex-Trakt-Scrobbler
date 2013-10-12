from sync import CollectionSync
from trakt import Trakt
import websocket


PLAYING_URL = 'http://localhost:32400/status/sessions/'

OPCODE_DATA = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)


class Scrobbler:
    playing = None

    def __init__(self):
        self.trakt = Trakt()
        self.ws = None

    def receive(self):
        frame = self.ws.recv_frame()

        if not frame:
            raise websocket.WebSocketException("Not a valid frame %s" % frame)
        elif frame.opcode in OPCODE_DATA:
            return frame.opcode, frame.data
        elif frame.opcode == websocket.ABNF.OPCODE_CLOSE:
            self.ws.send_close()
            return frame.opcode, None
        elif frame.opcode == websocket.ABNF.OPCODE_PING:
            self.ws.pong("Hi!")

        return None, None

    def scrobble(self, info):
        item = info['_children'][0]

        session_key = str(item['sessionKey'])
        state = str(item['state'])
        view_offset = str(item['viewOffset'])

        # Log.Debug(sessionKey + " - " + state + ' - ' + viewOffset)
        self.trakt.submit(session_key, state, view_offset)

    def update_collection(self, info):
        item = info['_children'][0]

        if item['type'] not in [1, 4]:
            return

        if item['state'] == 0:
            Log.Info("New File added to Libray: " + item['title'] + ' - ' + str(item['itemID']))

            # delay sync to wait for metadata
            Thread.CreateTimer(120, CollectionSync, True, item['itemID'], 'add')

        # #deleted file (doesn't work yet)
        # if item['state'] == 9:
        #     Log.Info("File deleted from Libray: " + item['title'] + ' - ' + str(item['itemID']))

        #     # delay sync to wait for metadata
        #     CollectionSync(item['itemID'], 'delete')

    def process(self, opcode, data):
        if opcode not in OPCODE_DATA:
            return

        info = JSON.ObjectFromString(data)

        if info['type'] == "playing" and Dict["scrobble"]:
            self.scrobble(info)

        if info['type'] == "timeline" and Dict['new_sync_collection']:
            self.update_collection(info)

    @route('/applications/trakttv/socketlisten')
    def listen(self):
        self.ws = websocket.create_connection('ws://localhost:32400/:/websockets/notifications')

        while True:
            self.process(*self.receive())
