import time
from trakt import Trakt


PLAYING_URL = 'http://localhost:32400/status/sessions/'


class Scrobbler:
    playing = None

    def __init__(self):
        self.trakt = Trakt()

    def stop_playing(self):
    # If the nothing is currently playing and this is not the first pass, mark the last item as stopped
        if self.playing is not None:
            self.playing['state'] = "stopped"

            self.trakt.submit(**self.playing)

            self.playing = None

    def update_playing(self):
        xml_file = HTTP.Request(PLAYING_URL)
        xml_content = XML.ElementFromString(xml_file).xpath('//Video')

        scrobble_users = Prefs['scrobble_users']
        scrobble_users = [su.strip() for su in scrobble_users.split(',')] if scrobble_users else None

        if len(xml_content) == 0:
            self.stop_playing()

        for media_container in xml_content:
            player = media_container.find('Player')
            user = media_container.find('User')

            if not scrobble_users or user.get('title') in scrobble_users:
                valid = True

                for key in ['ratingKey', 'viewOffset', 'duration']:
                    if key not in media_container or not media_container[key]:
                        valid = False
                        break

                if 'state' not in player or not player['state']:
                    valid = False

                # Submit playing state if valid
                if valid:
                    self.playing = {
                        'key': media_container.get('ratingKey'),
                        'state': player.get('state'),
                        'progress': round(float(media_container.get('viewOffset')) / int(media_container.get('duration')) * 100, 0)
                    }
                    self.trakt.submit(**self.playing)
            else:
                Log('User "%s" not in Scrobble users list, ignoring' % user.get('title'))

    @route('/applications/trakttv/scrobble_poll')
    def poll(self):
        while 1:
            if not Dict["scrobble"]:
                Log("Something went wrong... Exiting.")
                break

            self.update_playing()

            time.sleep(60)

        return
