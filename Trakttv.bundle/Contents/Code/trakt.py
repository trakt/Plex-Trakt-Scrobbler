import socket
import time
from plugin import PLUGIN_VERSION
from http import responses
from pms import PMS

TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28%s'


class Trakt:
    @classmethod
    @route('/applications/trakttv/trakt_request')
    def request(cls, action, values=None, param=''):
        if param != "":
            param = "/" + param
        data_url = TRAKT_URL % (action, param)

        if values is None:
            values = {}

        values['username'] = Prefs['username']
        values['password'] = Hash.SHA1(Prefs['password'])
        values['plugin_version'] = PLUGIN_VERSION
        values['media_center_version'] = Dict['server_version']

        try:
            json_file = HTTP.Request(data_url, data=JSON.StringFromObject(values))
            result = JSON.ObjectFromString(json_file.content)
        except socket.timeout:
            result = {'status': 'failure', 'error_code': 408, 'error': 'timeout'}
        except Ex.HTTPError, e:
            result = {'status': 'failure', 'error_code': e.code, 'error': responses[e.code][1]}
        except Ex.URLError, e:
            result = {'status': 'failure', 'error_code': 0, 'error': e.reason[0]}

        if 'status' in result:
            if result['status'] == 'success':
                if not 'message' in result:
                    if 'inserted' in result:
                        result['message'] = "%s Movies inserted, %s Movies already existed, %s Movies skipped" % (
                            result['inserted'], result['already_exist'], result['skipped']
                        )
                    else:
                        result['message'] = 'Unknown success'

                Log('Trakt responded with: %s' % result['message'])

                return {'status': True, 'message': result['message']}
            elif result['status'] == 'failure':
                Log('Trakt responded with: (%s) %s' % (result.get('error_code'), result.get('error')))

                return {'status': False, 'message': result['error'], 'result': result}

        Log('Return all')
        return {'result': result}

    @classmethod
    @route('/applications/trakttv/trakt_request_retry')
    def request_retry(cls, action, values, param='', max_retries=3, retry_sleep=30):
        result = cls.request(action, values, param)

        retry_num = 1
        while 'status' in result and not result['status'] and retry_num <= max_retries:
            if 'result' not in result:
                break
            if 'error_code' not in result['result']:
                break

            Log('Waiting %ss before retrying request' % retry_sleep)
            time.sleep(retry_sleep)

            if result['result']['error_code'] in [408, 504]:
                Log('Retrying request, retry #%s' % retry_num)
                result = cls.request(action, values, param)
                retry_num += 1
            else:
                break

        return result

    def get_media_type(self):
        # Is it a movie or a series? Else return false.
        if 'tvdb_id' in self.values:
            return 'show'
        elif 'imdb_id' or 'tmdb_id' in self.values:
            return 'movie'
        else:
            # Not a movie or TV-Show or have incorrect metadata!
            Log('Unknown item, bail out!')
            return None

    def watching(self):
        self.request(self.get_media_type() + '/watching', self.values)
        Log('sent "watching" request')

    def cancel_watching(self):
        self.request(self.get_media_type() + '/cancelwatching', self.values)
        Log('sent "cancelwatching" request')

    def scrobble(self):
        self.request_retry(self.get_media_type() + '/scrobble', self.values)
        Log('sent "scrobble" request')

    def submit(self, sessionKey, state, viewOffset):
        #fix for pht (not sending pause or stop when finished playing)
        #delete sessiondata if viewOffset is smaller than previous session viewOffset
        #we assume, that in this case it could be a new file.
        #if the user simply seeks backwards on the client, this is also triggered.
        if sessionKey in Dict['nowPlaying']:
            if 'prev_viewOffset' in Dict['nowPlaying'][sessionKey] and Dict['nowPlaying'][sessionKey]['prev_viewOffset'] > viewOffset:
                del Dict['nowPlaying'][sessionKey]
            else:
                Dict['nowPlaying'][sessionKey]['prev_viewOffset'] = viewOffset

        #skip over unkown items etc.
        if sessionKey in Dict['nowPlaying'] and 'skip' in Dict['nowPlaying'][sessionKey]:
            return

        if not sessionKey in Dict['nowPlaying']:
            Log.Info('getting MetaData for current media')

            try:
                xml_content = PMS.get_status().xpath('//MediaContainer/Video')

                for section in xml_content:
                    if section.get('sessionKey') == sessionKey and '/library/metadata' in section.get('key'):
                        Dict['nowPlaying'][sessionKey] = PMS.metadata(section.get('ratingKey'))

                        Dict['nowPlaying'][sessionKey]['UserName'] = ''
                        Dict['nowPlaying'][sessionKey]['UserID'] = ''

                        for user in section.findall('User'):
                            Dict['nowPlaying'][sessionKey]['UserName'] = user.get('title')
                            Dict['nowPlaying'][sessionKey]['UserID'] = user.get('id')

                        # setup some variables in Dict
                        Dict['nowPlaying'][sessionKey]['Last_updated'] = Datetime.FromTimestamp(0)
                        Dict['nowPlaying'][sessionKey]['scrobbled'] = False
                        Dict['nowPlaying'][sessionKey]['cur_state'] = state
                        Dict['nowPlaying'][sessionKey]['prev_viewOffset'] = 0

                # if session wasn't found, return False
                if not (sessionKey in Dict['nowPlaying']):
                    Log.Info('Session data not found')
                    return

            except Ex.HTTPError, e:
                Log.Error('Failed to connect to PMS.')
                return
            except Ex.URLError, e:
                Log.Error('Failed to connect to PMS.')
                return

        # Is it played by the correct user? Else return false

        if (Prefs['scrobble_names'] is not None) and (Prefs['scrobble_names'] != Dict['nowPlaying'][sessionKey]['UserName']):
            Log.Info('Ignoring item ('+Dict['nowPlaying'][sessionKey]['title']+') played by other user: '+Dict['nowPlaying'][sessionKey]['UserName'])
            Dict['nowPlaying'][sessionKey]['skip'] = True
            return

        # Is it a movie or a serie? Else return false
        if Dict['nowPlaying'][sessionKey]['type'] == 'episode' and Dict['nowPlaying'][sessionKey]['tvdb_id'] != False:
            action = 'show/'
        elif Dict['nowPlaying'][sessionKey]['type'] == 'movie' and (Dict['nowPlaying'][sessionKey]['imdb_id'] != False or Dict['nowPlaying'][sessionKey]['tmdb_id'] != False):
            action = 'movie/'
        else:
            # Not a movie or TV-Show or have incorrect metadata!
            Log.Info('Playing unknown item, will not be scrobbled: '+Dict['nowPlaying'][sessionKey]['title'])
            Dict['nowPlaying'][sessionKey]['skip'] = True
            return

        # calculate play progress
        Dict['nowPlaying'][sessionKey]['progress'] = int(round((float(viewOffset)/(Dict['nowPlaying'][sessionKey]['duration']*60*1000))*100, 0))

        if (state != Dict['nowPlaying'][sessionKey]['cur_state'] and state != 'buffering'):
            if (state == 'stopped') or (state == 'paused'):
                Log.Debug(Dict['nowPlaying'][sessionKey]['title']+' paused or stopped, cancel watching')
                action += 'cancelwatching'
            elif (state == 'playing'):
                Log.Debug('Updating watch status for '+Dict['nowPlaying'][sessionKey]['title'])
                action += 'watching'

        #scrobble item
        elif state == 'playing' and Dict['nowPlaying'][sessionKey]['scrobbled'] != True and Dict['nowPlaying'][sessionKey]['progress'] > 80:
            Log.Debug('Scrobbling '+Dict['nowPlaying'][sessionKey]['title'])
            action += 'scrobble'
            Dict['nowPlaying'][sessionKey]['scrobbled'] = True

        # update every 10 min
        elif state == 'playing' and ((Dict['nowPlaying'][sessionKey]['Last_updated'] + Datetime.Delta(minutes=10)) < Datetime.Now()):
            Log.Debug('Updating watch status for '+Dict['nowPlaying'][sessionKey]['title'])
            action += 'watching'

        else:
            # Already watching or already scrobbled
            Log.Debug('Nothing to do this time for '+Dict['nowPlaying'][sessionKey]['title'])
            return

        # Setup Data to send to Trakt
        values = dict()

        if Dict['nowPlaying'][sessionKey]['type'] == 'episode':
            values['tvdb_id'] = Dict['nowPlaying'][sessionKey]['tvdb_id']
            values['season'] = Dict['nowPlaying'][sessionKey]['season']
            values['episode'] = Dict['nowPlaying'][sessionKey]['episode']
        elif Dict['nowPlaying'][sessionKey]['type'] == 'movie':
            if (Dict['nowPlaying'][sessionKey]['imdb_id'] != False):
                values['imdb_id'] = Dict['nowPlaying'][sessionKey]['imdb_id']
            elif (Dict['nowPlaying'][sessionKey]['tmdb_id'] != False):
                values['tmdb_id'] = Dict['nowPlaying'][sessionKey]['tmdb_id']

        values['duration'] = Dict['nowPlaying'][sessionKey]['duration']
        values['progress'] = Dict['nowPlaying'][sessionKey]['progress']

        values['title'] = Dict['nowPlaying'][sessionKey]['title']
        if ('year' in Dict['nowPlaying'][sessionKey]):
            values['year'] = Dict['nowPlaying'][sessionKey]['year']

        self.request(action, values)

        Dict['nowPlaying'][sessionKey]['cur_state'] = state
        Dict['nowPlaying'][sessionKey]['Last_updated'] = Datetime.Now()

        #if just scrobbled, force update on next status update to set as watching again
        if action.find('scrobble') > 0:
            Dict['nowPlaying'][sessionKey]['Last_updated'] = Datetime.Now() - Datetime.Delta(minutes=20)

        # if stopped, remove data from Dict['nowPlaying']
        if (state == 'stopped' or state == 'paused'):
            del Dict['nowPlaying'][sessionKey] #delete session from Dict

        #make sure, that Dict is saved in case of plugin crash/restart
        Dict.Save()

        return
