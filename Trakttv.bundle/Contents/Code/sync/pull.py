from core.trakt import Trakt
from sync.sync_base import SyncBase


class Base(SyncBase):
    # TODO per-sync cached results, maybe core functionality in SyncBase?

    @staticmethod
    def get_trakt_library(media, marked, retry=True):
        # TODO maybe this could be moved to Trakt.Media class?
        return Trakt.request(
            'user/library/%s/%s.json' % (media, marked),
            param=Prefs['username'],

            retry=retry
        )

    @staticmethod
    def get_trakt_ratings(media, retry=True):
        # TODO maybe this could be moved to Trakt.Media class?
        return Trakt.request(
            'user/ratings/%s.json' % media,
            param=Prefs['username'],

            retry=retry
        )


class Show(Base):
    def run_watched(self):
        if Prefs['sync_watched'] is not True:
            Log.Debug('Ignoring watched sync, not enabled')
            return

        watched = self.get_trakt_library('shows', 'watched').get('data')
        Log.Debug('watched: %s' % watched)

    def run_ratings(self):
        if Prefs['sync_ratings'] is not True:
            Log.Debug('Ignoring ratings sync, not enabled')
            return

        ratings = self.get_trakt_ratings('episodes').get('data')
        Log.Debug('ratings: %s' % ratings)



class Movie(Base):
    def run(self):
        pass


class Pull(Base):
    children = [Show, Movie]
