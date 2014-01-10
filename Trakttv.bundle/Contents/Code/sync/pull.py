from core.logger import Logger
from sync.sync_base import SyncBase


log = Logger('sync.pull')


class Base(SyncBase):
    pass


class Show(Base):
    def run_watched(self):
        if Prefs['sync_watched'] is not True:
            log.debug('Ignoring watched sync, not enabled')
            return

        movies, shows = self.get_plex_library('show')

        watched = self.get_trakt_library('shows', 'watched')

        for item in watched:
            key = 'thetvdb', item.get('tvdb_id')
            
            if key is None or key not in shows:
                log.info('trakt watched item with key: %s, invalid or not in library', key)
                continue

            show = shows[key]

            log.debug('show: %s', show)
            log.debug('item: %s', item)

    # def run_ratings(self):
    #     if Prefs['sync_ratings'] is not True:
    #         log.debug('Ignoring ratings sync, not enabled')
    #         return
    #
    #     ratings = self.get_trakt_ratings('episodes').get('data')
    #     log.debug('ratings: %s' % ratings)


class Movie(Base):
    def run_watched(self):
        if Prefs['sync_watched'] is not True:
            log.debug('Ignoring watched sync, not enabled')
            return

        movies, shows = self.get_plex_library('movie')


class Pull(Base):
    children = [Show, Movie]
