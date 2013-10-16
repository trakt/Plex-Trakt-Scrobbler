from core.helpers import try_convert
from plex_api.media_server import PlexMediaServer
from plex_api.activity import ActivityMethod, PlexActivity
import websocket


class WebSocket(ActivityMethod):
    name = 'WebSocket'

    opcode_data = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)

    def __init__(self, now_playing):
        super(WebSocket, self).__init__(now_playing)

        self.ws = None

    @classmethod
    def test(cls):
        try:
            PlexMediaServer.request('status/sessions')
            return True
        except Ex.HTTPError:
            pass
        except Ex.URLError:
            pass

        Log.Info('%s method not available' % cls.name)
        return False

    def run(self):
        self.ws = websocket.create_connection('ws://localhost:32400/:/websockets/notifications')

        while True:
            self.process(*self.receive())

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

        info = JSON.ObjectFromString(data)
        item = info['_children'][0]

        if info['type'] == "playing" and Dict["scrobble"]:
            session_key = str(item['sessionKey'])
            state = str(item['state'])
            view_offset = try_convert(item['viewOffset'], int)

            self.scrobble(session_key, state, view_offset)

        if info['type'] == "timeline" and Dict['new_sync_collection']:
            if item['type'] not in [1, 4]:
                return

            if item['state'] == 0:
                Log.Info("New File added to Libray: " + item['title'] + ' - ' + str(item['itemID']))

                self.now_playing.update_collection(item['itemID'], 'add')

PlexActivity.register(WebSocket)
