import time
from trakt import watch_or_scrobble


@route('/applications/trakttv/scrobble')
def Scrobble():
    playing_url = 'http://localhost:32400/status/sessions/'
    previously_playing = False

    while 1:
        if not Dict["scrobble"]:
            Log("Something went wrong... Exiting.")
            break
        else: pass

        xml_file = HTTP.Request(playing_url)
        xml_content = XML.ElementFromString(xml_file).xpath('//Video')
        try:
            player = xml_content[0].find('Player')
            playing = {
                'key': xml_content[0].get('ratingKey'),
                'state': player.get('state'),
                'progress': round(float(xml_content[0].get('viewOffset')) / int(xml_content[0].get('duration')) * 100, 0)
            }
            previously_playing = True
            watch_or_scrobble(playing)

        except:
            # If the nothing is currently playing and this is not the first pass, mark the last item as stopped
            if previously_playing:
                playing['state'] = "stopped"
                watch_or_scrobble(playing)
                previously_playing = False
            else:
                pass

        time.sleep(60)

    return
