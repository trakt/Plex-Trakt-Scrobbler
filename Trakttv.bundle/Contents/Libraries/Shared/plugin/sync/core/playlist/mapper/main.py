from plugin.sync.core.playlist.mapper.handlers import PlexPlaylistHandler, TraktPlaylistHandler

from plex import Plex
import logging
import trakt.objects as t_objects

log = logging.getLogger(__name__)


class PlaylistMapper(object):
    def __init__(self, task, p_sections_map):
        self.task = task
        self.p_sections_map = p_sections_map

        self.plex = PlexPlaylistHandler(self.task)
        self.trakt = TraktPlaylistHandler(self.task)

    def expand(self, t_item):
        t_type = type(t_item)

        if t_type is t_objects.Show:
            return self.expand_show(t_item)

        if t_type is t_objects.Season:
            return self.expand_season(t_item)

        raise ValueError('Unknown item type: %r' % t_type)

    def expand_show(self, t_show):
        t_client = getattr(t_show, '_client', None)

        # Retrieve plex show that matches `t_season`
        p_keys = list(self.task.map.by_guid(t_show.pk))

        if len(p_keys) < 1:
            log.info('Unable to find show that matches guid: %r', t_show.pk)
            return t_show

        p_section_key, p_show_key = p_keys[0]

        # Retrieve plex episodes that matches `t_show`
        t_episodes = {}

        for p_episode in Plex['library/metadata'].all_leaves(p_show_key):
            p_season = p_episode.season

            t_season = t_objects.Season(t_client, [p_season.index], t_show.index)
            t_season.show = t_show

            t_episode = t_objects.Episode(t_client, [(p_season.index, p_episode.index)], t_show.index)
            t_episode.show = t_show
            t_episode.season = t_season

            if p_season.index not in t_episodes:
                t_episodes[p_season.index] = {}

            t_episodes[p_season.index][p_episode.index] = t_episode

        # Update trakt table
        self.trakt.table[t_show.pk] = t_episodes

        return t_episodes

    def expand_season(self, t_season):
        t_client = getattr(t_season, '_client', None)
        t_show = t_season.show

        # Retrieve plex show that matches `t_season`
        p_keys = list(self.task.map.by_guid(t_show.pk))

        if len(p_keys) < 1:
            log.info('Unable to find show that matches guid: %r', t_show.pk)
            return t_season

        p_section_key, p_show_key = p_keys[0]

        # Retrieve plex season that matches `t_season`
        p_seasons = dict([
            (p_season.index, p_season)
            for p_season in Plex['library/metadata'].children(p_show_key)
        ])

        p_season = p_seasons.get(t_season.pk)

        if p_season is None:
            log.info('Unable to find season that matches pk: %r', t_season.pk)
            return t_season

        # Create dummy trakt episodes that matches the available plex episodes
        t_episodes = {}

        for p_episode in p_season.children():
            t_episode = t_objects.Episode(t_client, [(p_season.index, p_episode.index)], t_season.index)
            t_episode.show = t_season.show
            t_episode.season = t_season

            t_episodes[p_episode.index] = t_episode

        # Update trakt table
        self.trakt.table[t_show.pk][p_season.index] = t_episodes

        return t_episodes

    def get(self, key):
        p_item = self.plex.get(*key) or (None, None)
        t_item = self.trakt.get(*key)

        if type(t_item) in [t_objects.Show, t_objects.Season]:
            t_item = self.expand(t_item)

        return p_item, t_item

    def match(self):
        t_items = []
        p_items = []

        # Iterate over trakt keys, sort by index
        t_keys = self.trakt.keys_ordered()
        t_keys_matched = []

        index = 0

        for t_index, key in enumerate(t_keys):
            p_item, t_item = self.get(key)

            for key, (p_index, p_item), t_item in self.select(key, p_item, t_item):
                t_keys_matched.append(key)

                t_items.append((key, index, (p_index, p_item), (t_index, t_item)))
                index += 1

        # Iterate over plex keys (that aren't in trakt)
        p_keys = set(self.plex.items.keys()) - set(t_keys_matched)

        for x, key in enumerate(p_keys):
            p_item, t_item = self.get(key)

            for key, (p_index, p_item), t_item in self.select(key, p_item, t_item):
                t_keys_matched.append(key)

                p_items.append((key, index, (p_index, p_item), (None, t_item)))
                index += 1

        return t_items, p_items

    def select(self, base_key, p_items, t_items):
        p_type = type(p_items)
        t_type = type(t_items)

        if p_type is not dict or t_type is not dict:
            yield base_key, p_items, t_items
            return

        # Iterate over dictionaries
        keys = set(p_items.keys()) | set(t_items.keys())

        for i_key in keys:
            key = base_key + (i_key,)
            p_item = p_items.get(i_key, (None, None))
            t_item = t_items.get(i_key)

            for item in self.select(key, p_item, t_item):
                yield item
