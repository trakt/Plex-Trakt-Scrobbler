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

        movies, shows = self.plex.library('show')

        watched = self.trakt.library('shows', 'watched')

        for item in watched:
            log.debug('item: %s', item)

            key = 'thetvdb', item.get('tvdb_id')
            
            if key is None or key not in shows:
                log.info('trakt watched item with key: %s, invalid or not in library', key)
                continue

            if 'seasons' not in item:
                log.warn('Watched item is missing "seasons" data, ignoring')
                continue

            for show in shows[key]:
                self.update_show_watched(item, show)

    def update_show_watched(self, item, show):
        show_seasons = self.plex.episodes(show.key)

        for season, episodes in [(x.get('season'), x.get('episodes')) for x in item['seasons']]:

            if season not in show_seasons:
                log.info('S%02d is missing from plex library', season)
                continue

            show_episodes = show_seasons[season]

            for episode in episodes:
                if episode not in show_episodes:
                    log.info('S%02dE%02d is missing from plex library', season, episode)
                    continue

                show_episode = show_episodes[episode]

                # Ignore already seen episodes
                if show_episode.seen:
                    continue

                log.info('TODO: mark episode S%02dE%02d seen, ratingKey: "%s"', season, episode, show_episode.key)

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

        movies, shows = self.plex.library('movie')


class Pull(Base):
    children = [Show, Movie]
