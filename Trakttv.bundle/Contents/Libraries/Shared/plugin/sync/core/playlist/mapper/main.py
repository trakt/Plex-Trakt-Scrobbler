from plugin.sync.core.playlist.mapper.handlers import PlexPlaylistHandler, TraktPlaylistHandler


class PlaylistMapper(object):
    def __init__(self, task, p_sections_map):
        self.task = task
        self.p_sections_map = p_sections_map

        self.plex = PlexPlaylistHandler(self.task)
        self.trakt = TraktPlaylistHandler(self.task)

    def match(self):
        # Iterate over trakt keys, sort by index
        t_keys = self.trakt.keys_ordered()
        t_count = len(t_keys)

        for index, key in enumerate(t_keys):
            p_item = self.plex.get(*key)
            t_item = self.trakt.get(*key)

            yield key, index, p_item, t_item

        # Iterate over plex keys (that aren't in trakt)
        p_keys = set(self.plex.items.keys()) - set(t_keys)

        for index, key in enumerate(p_keys):
            p_item = self.plex.get(*key)
            t_item = self.trakt.get(*key)

            yield key, t_count + index, p_item, t_item
