from core.logger import Logger
from plex.media_server_new import PlexMediaServer
from sync.sync_base import SyncBase


log = Logger('sync.pull')


class Base(SyncBase):
    pass


class Episode(Base):
    key = 'episode'

    auto_run = False

    def run_watched(self, season_num, p_episodes, t_episodes):
        for t_episode_num in t_episodes:
            # Check if episode exists in plex library
            if t_episode_num not in p_episodes:
                log.info('S%02dE%02d is missing from plex library', season_num, t_episode_num)
                continue

            p_episode = p_episodes[t_episode_num]

            # Ignore already seen episodes
            if p_episode.seen:
                continue

            PlexMediaServer.scrobble(p_episode.key)


class Season(Base):
    key = 'season'

    children = [Episode]
    auto_run = False

    def run_watched(self, p_seasons, t_seasons):
        for t_season_num, t_episodes in [(x.get('season'), x.get('episodes')) for x in t_seasons]:
            # Check if season exists in plex library
            if t_season_num not in p_seasons:
                log.info('S%02d is missing from plex library', t_season_num)
                continue

            # Pass on to Episode task
            self.trigger('episode', 'watched',
                season_num=t_season_num,
                p_episodes=p_seasons[t_season_num],
                t_episodes=t_episodes
            )


class Show(Base):
    key = 'show'

    children = [Season]

    def run_watched(self):
        if Prefs['sync_watched'] is not True:
            log.debug('Ignoring watched sync, not enabled')
            return

        _, p_shows = self.plex.library('show')

        watched = self.trakt.library('shows', 'watched')

        for item in watched:
            log.info('Updating watched states for "%s"', item.get('title'))

            key = 'thetvdb', item.get('tvdb_id')
            
            if key is None or key not in p_shows:
                log.info('trakt watched item with key: %s, invalid or not in library', key)
                continue

            if 'seasons' not in item:
                log.warn('Watched item is missing "seasons" data, ignoring')
                continue

            for p_show in p_shows[key]:
                self.trigger('season', 'watched',
                    p_seasons=self.plex.episodes(p_show.key),
                    t_seasons=item['seasons']
                )

    # def run_ratings(self):
    #     if Prefs['sync_ratings'] is not True:
    #         log.debug('Ignoring ratings sync, not enabled')
    #         return
    #
    #     ratings = self.get_trakt_ratings('episodes').get('data')
    #     log.debug('ratings: %s' % ratings)


class Movie(Base):
    key = 'movie'

    def run_watched(self):
        if Prefs['sync_watched'] is not True:
            log.debug('Ignoring watched sync, not enabled')
            return

        movies, _ = self.plex.library('movie')


class Pull(Base):
    children = [Show, Movie]
