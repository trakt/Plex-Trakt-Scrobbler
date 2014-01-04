from sync.sync_base import SyncBase


class Base(SyncBase):
    pass


class Show(Base):
    def run_watched(self):
        if Prefs['sync_watched'] is not True:
            Log.Debug('Ignoring watched sync, not enabled')
            return

        library = self.get_plex_library('show')

        #watched = self.get_trakt_library('shows', 'watched').get('data')
        #Log.Debug('watched: %s' % watched)

    # def run_ratings(self):
    #     if Prefs['sync_ratings'] is not True:
    #         Log.Debug('Ignoring ratings sync, not enabled')
    #         return
    #
    #     ratings = self.get_trakt_ratings('episodes').get('data')
    #     Log.Debug('ratings: %s' % ratings)



class Movie(Base):
    def run_watched(self):
        if Prefs['sync_watched'] is not True:
            Log.Debug('Ignoring watched sync, not enabled')
            return

        library = self.get_plex_library('movie')


class Pull(Base):
    children = [Show, Movie]
