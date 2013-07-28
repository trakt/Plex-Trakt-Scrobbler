from plugin import PLUGIN_VERSION
from pms import get_metadata_from_pms
from http import responses

TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28%s'


@route('/applications/trakttv/talk_to_trakt')
def talk_to_trakt(action, values, param=''):

    if param != "":
        param = "/" + param
        # Function to talk to the trakt.tv api.
    data_url = TRAKT_URL % (action, param)

    try:
        json_file = HTTP.Request(data_url, data=JSON.StringFromObject(values))
        #headers = json_file.headers
        result = JSON.ObjectFromString(json_file.content)
        #Log(result)

    except Ex.HTTPError, e:
        result = {'status': 'failure', 'error': responses[e.code][1]}
    except Ex.URLError, e:
        return {'status': 'failure', 'error': e.reason[0]}

    try:
        if result['status'] == 'success':
            if not 'message' in result:
                result['message'] = 'Unknown success'
            Log('Trakt responded with: %s' % result['message'])
            return {'status' : True, 'message' : result['message']}
        elif result['status'] == 'failure':
            Log('Trakt responded with: %s' % result['error'])
            return {'status' : False, 'message' : result['error']}
    except:
        Log('Return all')
        return result

@route('/applications/trakttv/watch_or_scrobble')
def watch_or_scrobble(log_values):
    # Function to add what currently is playing to trakt, decide to watch or scrobble.
    LAST_USED_ID = Dict['Last_used_id']
    LAST_USED_ACTION = Dict['Last_used_action']
    values = Dict['Last_used_metadata']
    LAST_UPDATED = Dict['Last_updated']
    Log('Current id: %s and previous id: %s using action: %s' % (log_values['key'], LAST_USED_ID, LAST_USED_ACTION))

    if log_values['key'] != LAST_USED_ID:
        # Reset all parameters since the user has changed what they are watching.
        Log('Lets refresh the metadata')
        values = get_metadata_from_pms(log_values['key'])
        Dict['Last_used_metadata'] = values
        Dict['Last_used_id'] = log_values['key']
        LAST_USED_ACTION = None
        LAST_UPDATED = None

    values['progress'] = log_values['progress']

    # Add username and password to values.
    values['username'] = Prefs['username']
    values['password'] = Hash.SHA1(Prefs['password'])
    values['plugin_version'] = PLUGIN_VERSION
    # TODO
    values['media_center_version'] = '%s, %s' % (Platform.OS, Platform.CPU)

    # Is it a movie or a series? Else return false.
    if 'tvdb_id' in values:
        action = 'show/'
    elif 'imdb_id' or 'tmdb_id' in values:
        action = 'movie/'
    else:
        # Not a movie or TV-Show or have incorrect metadata!
        Log('Unknown item, bail out!')
        return False

    if (log_values['key'] != LAST_USED_ID) or (LAST_USED_ACTION == 'cancel' and log_values['state'] == 'playing'):
        action += 'watching'
        USED_ACTION = 'watching'
        Dict['Last_updated'] = Datetime.Now()
    elif LAST_USED_ACTION == 'watching' and (LAST_UPDATED + Datetime.Delta(minutes=10)) < Datetime.Now() and values['progress'] < 80:
        Log('More than 10 minutes since last update')
        action += 'watching'
        USED_ACTION = 'watching'
        Dict['Last_updated'] = Datetime.Now()
    elif LAST_USED_ACTION == 'watching' and values['progress'] > 80:
        action += 'scrobble'
        USED_ACTION = 'scrobble'
    elif LAST_USED_ACTION == 'watching' and log_values['state'] == 'stopped':
        action += 'cancelwatching'
        USED_ACTION = 'cancel'
    else:
        # Already watching or already scrobbled.
        Log('Nothing to do this time, all that could be done is done!')
        return False

    result = talk_to_trakt(action, values)
    # Only update the action if trakt responds with a success.
    if result['status']:
        Dict['Last_used_action'] = USED_ACTION

    return result
