from plugin import PLUGIN_VERSION
from pms import get_metadata_from_pms
from http import responses

TRAKT_URL = 'http://api.trakt.tv/%s/ba5aa61249c02dc5406232da20f6e768f3c82b28%s'


class Trakt:
    def __init__(self):
        self.reload()

    @classmethod
    @route('/applications/trakttv/trakt_request')
    def request(cls, action, values, param=''):
        if param != "":
            param = "/" + param
        data_url = TRAKT_URL % (action, param)

        try:
            json_file = HTTP.Request(data_url, data=JSON.StringFromObject(values))
            result = JSON.ObjectFromString(json_file.content)
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

    def fill(self, values):
        values['username'] = Prefs['username']
        values['password'] = Hash.SHA1(Prefs['password'])
        values['plugin_version'] = PLUGIN_VERSION
        values['media_center_version'] = '%s, %s' % (Platform.OS, Platform.CPU)

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
        self.request(self.get_media_type() + '/scrobble', self.values)
        Log('sent "scrobble" request')

    def reload(self):
        self.last_id = Dict['last_used_id']
        self.last_updated = Dict['last_updated']
        self.is_watching = Dict['is_watching']
        self.scrobbled = Dict['scrobbled']
        self.values = Dict['last_used_metadata']

    def save(self):
        Dict['last_used_id'] = self.last_id
        Dict['last_updated'] = self.last_updated
        Dict['is_watching'] = self.is_watching
        Dict['scrobbled'] = self.scrobbled
        Dict['last_used_metadata'] = self.values

    @route('/applications/trakttv/trakt_submit')
    def submit(self, key, state, progress):
        self.reload()

        # Function to add what currently is playing to trakt, decide to watch or scrobble.
        Log('Current id: %s and previous id: %s' % (key, self.last_id))

        if key != self.last_id:
            # Check if we have something leftover to scrobble
            if self.is_watching and not self.scrobbled and self.values['progress'] > 80:
                self.scrobble()
                self.scrobbled = True
                Log('Scrobbled leftovers')

            # Reset all parameters since the user has changed what they are watching.
            Log('Lets refresh the metadata')
            self.values = get_metadata_from_pms(key)
            self.last_id = key
            self.last_updated = None
            self.scrobbled = False
            self.is_watching = False
            self.save()

        # Fill with current account details and progress
        self.fill(self.values)
        self.values['progress'] = progress

        # Started watching
        if (key != self.last_id) or (not self.is_watching and state == 'playing'):
            self.watching()
            self.is_watching = True
            self.last_updated = Datetime.Now()

        # Update watching every 10 minutes
        if self.is_watching and (self.last_updated + Datetime.Delta(minutes=10)) < Datetime.Now():
            Log('More than 10 minutes since last update')
            self.watching()
            self.last_updated = Datetime.Now()

        # Scrobble when we hit 80% watched
        if self.values['progress'] > 98 and not self.scrobbled:
            self.scrobble()
            self.scrobbled = True

        # Cancel watching if playback has stopped
        if self.is_watching and state == 'stopped':
            # Scrobble leftovers
            if not self.scrobbled and self.values['progress'] > 80:
                self.scrobble()
                self.scrobbled = True
                Log('Scrobbled leftovers')
            else:
                self.cancel_watching()

            self.is_watching = False

        self.save()
