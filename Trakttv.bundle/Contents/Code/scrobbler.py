from sync import CollectionSync
from trakt import Trakt
import websocket


PLAYING_URL = 'http://localhost:32400/status/sessions/'

OPCODE_DATA = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)


class Scrobbler:
    playing = None

    def __init__(self):
        self.trakt = Trakt()

    @route('/applications/trakttv/socketlisten')
    def listen(self):
        ws = websocket.create_connection('ws://localhost:32400/:/websockets/notifications')

        def SocketRecv():
            frame = ws.recv_frame()
            if not frame:
                raise websocket.WebSocketException("Not a valid frame %s" % frame)
            elif frame.opcode in OPCODE_DATA:
                return (frame.opcode, frame.data)
            elif frame.opcode == websocket.ABNF.OPCODE_CLOSE:
                ws.send_close()
                return (frame.opcode, None)
            elif frame.opcode == websocket.ABNF.OPCODE_PING:
                ws.pong("Hi!")

            return None, None

        while True:
            opcode, data = SocketRecv()
            msg = None
            if opcode in OPCODE_DATA:
                info = JSON.ObjectFromString(data)

                #scrobble
                if info['type'] == "playing" and Dict["scrobble"]:
                    sessionKey = str(info['_children'][0]['sessionKey'])
                    state = str(info['_children'][0]['state'])
                    viewOffset = str(info['_children'][0]['viewOffset'])
                    # Log.Debug(sessionKey + " - " + state + ' - ' + viewOffset)
                    self.trakt.submit(sessionKey, state, viewOffset)

                #adding to collection
                elif info['type'] == "timeline" and Dict['new_sync_collection']:
                    if (info['_children'][0]['type'] == 1 or info['_children'][0]['type'] == 4) and info['_children'][0]['state'] == 0:
                        Log.Info("New File added to Libray: " + info['_children'][0]['title'] + ' - ' + str(info['_children'][0]['itemID']))
                        itemID = info['_children'][0]['itemID']
                        # delay sync to wait for metadata
                        Thread.CreateTimer(120, CollectionSync, True, itemID, 'add')

                        # #deleted file (doesn't work yet)
                        # elif (info['_children'][0]['type'] == 1 or info['_children'][0]['type'] == 4) and info['_children'][0]['state'] == 9:
                        #     Log.Info("File deleted from Libray: " + info['_children'][0]['title'] + ' - ' + str(info['_children'][0]['itemID']))
                        #     itemID = info['_children'][0]['itemID']
                        #     # delay sync to wait for metadata
                        #     CollectionSync(itemID,'delete')

        return
