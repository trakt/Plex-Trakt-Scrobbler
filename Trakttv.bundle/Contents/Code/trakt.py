import socket
import time
from plugin import PLUGIN_VERSION
from http import responses
from pms import PMS

TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28%s'


class Trakt:
    def __init__(self):
        pass

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
    def request_retry(cls, action, values=None, param='', max_retries=3, retry_sleep=30):
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

    def create_session(self, sessionKey, state):
        Log.Info('getting MetaData for current media')

        try:
            xml_content = PMS.get_status().xpath('//MediaContainer/Video')

            for section in xml_content:
                if section.get('sessionKey') == sessionKey and '/library/metadata' in section.get('key'):
                    session = PMS.metadata(section.get('ratingKey'))

                    session['UserName'] = ''
                    session['UserID'] = ''

                    for user in section.findall('User'):
                        session['UserName'] = user.get('title')
                        session['UserID'] = user.get('id')

                    # setup some variables in Dict
                    session['Last_updated'] = Datetime.FromTimestamp(0)
                    session['scrobbled'] = False
                    session['cur_state'] = state
                    session['prev_viewOffset'] = 0

                    # store session in nowPlaying state
                    Dict['nowPlaying'][sessionKey] = session

            # if session wasn't found, return False
            if sessionKey not in Dict['nowPlaying']:
                Log.Info('Session data not found')
                return None

            return Dict['nowPlaying'][sessionKey]

        except Ex.HTTPError:
            Log.Error('Failed to connect to PMS.')
            return None
        except Ex.URLError:
            Log.Error('Failed to connect to PMS.')
            return None

    def get_media_type(self, session):
        if not session or not session.get('type'):
            return None

        if session.get('type') == 'episode' and session['tvdb_id']:
            return 'show'
        elif session.get('type') == 'movie' and (session['imdb_id'] or session['tmdb_id']):
            return 'movie'

        return None

    def get_action(self, session, state):
        if state not in [session['cur_state'], 'buffering']:
            if state in ['stopped', 'paused']:
                Log.Debug(session['title'] + ' paused or stopped, cancel watching')
                return 'cancelwatching'

            if state == 'playing':
                Log.Debug('Updating watch status for ' + session['title'])
                return 'watching'

        #scrobble item
        elif state == 'playing' and not session['scrobbled'] and session['progress'] > 80:
            Log.Debug('Scrobbling ' + session['title'])
            return 'scrobble'

        # update every 10 min
        elif state == 'playing' and ((session['Last_updated'] + Datetime.Delta(minutes=10)) < Datetime.Now()):
            Log.Debug('Updating watch status for ' + session['title'])
            return 'watching'

        return None

    def get_session_values(self, session):
        values = {}

        if session['type'] == 'episode':
            values['tvdb_id'] = session['tvdb_id']
            values['season'] = session['season']
            values['episode'] = session['episode']

        if session['type'] == 'movie':
            if session['imdb_id']:
                values['imdb_id'] = session['imdb_id']
            elif session['tmdb_id']:
                values['tmdb_id'] = session['tmdb_id']

        values['duration'] = session['duration']
        values['progress'] = session['progress']

        values['title'] = session['title']

        if 'year' in session:
            values['year'] = session['year']

        return values

    def submit(self, sessionKey, state, viewOffset):
        session = Dict['nowPlaying'].get(sessionKey)

        # fix for pht (not sending pause or stop when finished playing)
        # delete sessiondata if viewOffset is smaller than previous session viewOffset
        # we assume, that in this case it could be a new file.
        # if the user simply seeks backwards on the client, this is also triggered.

        if session:
            if 'prev_viewOffset' in session and session['prev_viewOffset'] > viewOffset:
                del Dict['nowPlaying'][sessionKey]
                session = None
            else:
                session['prev_viewOffset'] = viewOffset

            #skip over unkown items etc.
            if 'skip' in session:
                return

        if not session:
            session = self.create_session(sessionKey, state)
            if not session:
                Log.Info('Invalid session, unable to continue')
                return

        # Is it played by the correct user? Else return false
        if (Prefs['scrobble_names'] is not None) and (Prefs['scrobble_names'] != session['UserName']):
            Log.Info('Ignoring item (' + session['title'] + ') played by other user: ' + session['UserName'])
            session['skip'] = True
            return

        # Is it a movie or a serie? Else return false
        media_type = self.get_media_type(session)

        # Not a movie or TV-Show or have incorrect metadata!
        if not media_type:
            Log.Info('Playing unknown item, will not be scrobbled: ' + session['title'])
            session['skip'] = True
            return

        # calculate play progress
        session['progress'] = int(round((float(viewOffset) / (session['duration'] * 60 * 1000)) * 100, 0))

        action = self.get_action(session, state)
        if not action:
            # Already watching or already scrobbled
            Log.Debug('Nothing to do this time for ' + session['title'])
            return

        if action == 'scrobble':
            session['scrobbled'] = True

        # Setup Data to send to Trakt
        values = self.get_session_values(session)

        if action == 'scrobble':
            # Ensure scrobbles are submitted, retry on network timeouts
            self.request_retry(media_type + '/' + action, values)
        else:
            self.request(media_type + '/' + action, values)

        session['cur_state'] = state
        session['Last_updated'] = Datetime.Now()

        #if just scrobbled, force update on next status update to set as watching again
        if action == 'scrobble':
            session['Last_updated'] = Datetime.Now() - Datetime.Delta(minutes=20)

        # if stopped, remove data from Dict['nowPlaying']
        if state in ['stopped', 'paused']:
            del Dict['nowPlaying'][sessionKey]  # delete session from Dict

        #make sure, that Dict is saved in case of plugin crash/restart
        Dict.Save()
