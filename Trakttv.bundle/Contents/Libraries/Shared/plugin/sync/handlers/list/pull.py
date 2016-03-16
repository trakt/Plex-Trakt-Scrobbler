from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, MediaHandler, bind

from plex import Plex
import logging
import urllib

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, **kwargs):
        return kwargs

    def get_action(self, p_item, t_item):
        if not p_item and t_item:
            return 'added'

        if p_item and not t_item:
            return 'removed'

        return None

    def fast_pull(self, action=None, **kwargs):
        if action is None:
            # Determine performed action
            action = self.get_action(kwargs['p_item'], kwargs['t_item'])

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(action, **kwargs)

    def pull(self, key, p_item, t_item, *args, **kwargs):
        # Determine performed action
        action = self.get_action(p_item, t_item)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(
            action,

            key=key,

            p_item=p_item,
            t_item=t_item,
            **kwargs
        )

    #
    # Action handlers
    #

    @bind('added')
    def on_added(self, p_sections_map, p_playlist, key, p_item, t_item):
        # Find item in plex matching `t_item`
        p_key = self.match(type(t_item), *key)

        if p_key is None:
            return

        log.debug('%s.on_added(p_key: %r)', self.media, p_key)

        # Build uri for plex item
        uri = self.build_uri(p_sections_map, *p_key)

        # Add item to playlist
        p_playlist.add(uri)

    #
    # Helpers
    #

    @staticmethod
    def build_uri(p_sections_map, p_section_key, p_item_key):
        # Retrieve section UUID
        p_section_uuid = p_sections_map.get(p_section_key)

        # Build URI
        return 'library://%s/item/%s' % (
            p_section_uuid,
            urllib.quote_plus('/library/metadata/%s' % p_item_key)
        )

    def match(self, t_type, key, *extra):
        # Try retrieve `pk` for `key`
        pk = self.current.state.trakt.table(t_type).get(key)

        if pk is None:
            pk = key

        # Retrieve plex items that match `pk`
        p_keys = self.current.map.by_guid(pk)

        if not p_keys:
            return None

        # Convert to list (for indexing)
        p_keys = list(p_keys)

        # Use first match found in plex
        p_section_key, p_item_key = p_keys[0]

        # Find season/episode
        if len(extra) > 0:
            return self.match_show(p_section_key, p_item_key, *extra)

        return p_section_key, p_item_key

    def match_show(self, p_section_key, p_show_key, season, episode=None):
        # Fetch seasons for show
        p_seasons = dict([
            (p_season.index, p_season.rating_key)
            for p_season in Plex['library/metadata'].children(p_show_key)
        ])

        # Find matching season
        p_season_key = p_seasons.get(season)

        if p_season_key is None:
            # Unable to find season
            return None

        if episode is None:
            # Return matching season
            return p_section_key, p_season_key

        # Fetch episodes for season
        p_episodes = dict([
            (p_episode.index, p_episode.rating_key)
            for p_episode in Plex['library/metadata'].children(p_season_key)
        ])

        # Find matching episode
        p_episode_key = p_episodes.get(episode)

        if p_episode_key is None:
            # Unable to find episode
            return None

        # Return matching episode
        return p_section_key, p_episode_key


class Lists(MediaHandler):
    media = SyncMedia.Lists

    @staticmethod
    def build_action(action, **kwargs):
        return kwargs

    def fast_pull(self, action, **kwargs):
        # Execute action
        self.execute_action(action, **kwargs)

    @bind('added')
    def on_added(self, key, **kwargs):
        log.debug('%s.on_added(key: %r, kwargs: %r)', self.media, key, kwargs)

    @bind('changed')
    def on_changed(self, key, **kwargs):
        log.debug('%s.on_changed(key: %r, kwargs: %r)', self.media, key, kwargs)


class Movies(Base):
    media = SyncMedia.Movies


class Shows(Base):
    media = SyncMedia.Shows


class Seasons(Base):
    media = SyncMedia.Seasons


class Episodes(Base):
    media = SyncMedia.Episodes


class Pull(DataHandler):
    data = [
        SyncData.Liked,
        SyncData.Personal,
        SyncData.Watchlist
    ]

    mode = [
        SyncMode.FastPull,
        SyncMode.Pull
    ]

    children = [
        Lists,

        Movies,
        Shows,
        Seasons,
        Episodes
    ]
