import time
from trakt import Trakt


PLAYING_URL = 'http://localhost:32400/status/sessions/'


class Scrobbler:
    playing = None

    def __init__(self):
        self.trakt = Trakt()

    def update_playing(self):
        xml_file = HTTP.Request(PLAYING_URL)
        xml_content = XML.ElementFromString(xml_file).xpath('//Video')

        try:
            player = xml_content[0].find('Player')

            self.playing = {
                'key': xml_content[0].get('ratingKey'),
                'state': player.get('state'),
                'progress': round(float(xml_content[0].get('viewOffset')) / int(xml_content[0].get('duration')) * 100, 0)
            }
            self.trakt.submit(**self.playing)
        except:  # TODO replace 'except' with proper checks
            # If the nothing is currently playing and this is not the first pass, mark the last item as stopped
            if self.playing is not None:
                self.playing['state'] = "stopped"

                self.trakt.submit(**self.playing)

                self.playing = None

    @route('/applications/trakttv/scrobble_poll')
    def poll(self):
        while 1:
            if not Dict["scrobble"]:
                Log("Something went wrong... Exiting.")
                break

            self.update_playing()

            time.sleep(60)

        return
