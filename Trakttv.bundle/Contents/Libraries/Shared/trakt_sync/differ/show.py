from trakt_sync.differ.core.base import Differ
from trakt_sync.differ.core.helpers import dict_path
from trakt_sync.differ.handlers import Collection, Playback, Rating, Watched


class ShowDiffer(Differ):
    def __init__(self):
        self.season = SeasonDiffer()

        self.handlers = [
            h(self) for h in [
                Rating
            ]
        ]

    def run(self, base, current):
        keys_base = set(base.keys())
        keys_current = set(current.keys())

        changes = {}

        for key in keys_current - keys_base:
            actions = self.process_added(current[key])

            self.store_actions(changes, actions)

        for key in keys_base - keys_current:
            actions = self.process_removed(base[key])

            self.store_actions(changes, actions)

        for key in keys_base & keys_current:
            actions = self.process_common(base[key], current[key])

            self.store_actions(changes, actions)

        # Run season differ on shows
        for key in keys_base | keys_current:
            b = base.get(key)
            c = current.get(key)

            self.season.run(
                b.seasons if b else {},
                c.seasons if c else {},
                changes=changes
            )

        return changes


class SeasonDiffer(Differ):
    def __init__(self):
        self.episode = EpisodeDiffer()

        self.handlers = [
            h(self) for h in [
                Rating
            ]
        ]

    def run(self, base, current, changes=None):
        keys_base = set(base.keys())
        keys_current = set(current.keys())

        if changes is None:
            changes = {}

        for key in keys_current - keys_base:
            actions = self.process_added(current[key])

            self.store_season_actions(changes, current[key], actions)

        for key in keys_base - keys_current:
            actions = self.process_removed(base[key])

            self.store_season_actions(changes, base[key], actions)

        for key in keys_base & keys_current:
            actions = self.process_common(base[key], current[key])

            self.store_season_actions(changes, current[key], actions)

        # Run episode differ on seasons
        for key in keys_base | keys_current:
            b = base.get(key)
            c = current.get(key)

            self.episode.run(
                b.episodes if b else {},
                c.episodes if c else {},
                changes=changes
            )

        return changes

    @classmethod
    def store_season_actions(cls, changes, season, actions):
        for action in actions:
            cls.store_season_action(changes, season, *action)

    @classmethod
    def store_season_action(cls, changes, season, key, collection, action, properties=None):
        show = season.show

        seasons = dict_path(changes, (
            collection, action, show.pk,
            'seasons',
        ))

        seasons[key] = properties


class EpisodeDiffer(Differ):
    def __init__(self):
        self.handlers = [
            h(self) for h in [
                Collection,
                Playback,
                Rating,
                Watched
            ]
        ]

    def run(self, base, current, changes=None):
        keys_base = set(base.keys())
        keys_current = set(current.keys())

        if changes is None:
            changes = {}

        for key in keys_current - keys_base:
            actions = self.process_added(current[key])

            self.store_episode_actions(changes, current[key], actions)

        for key in keys_base - keys_current:
            actions = self.process_removed(base[key])

            self.store_episode_actions(changes, base[key], actions)

        for key in keys_base & keys_current:
            actions = self.process_common(base[key], current[key])

            self.store_episode_actions(changes, current[key], actions)

        return changes

    @classmethod
    def store_episode_actions(cls, changes, episode, actions):
        for action in actions:
            cls.store_episode_action(changes, episode, *action)

    @classmethod
    def store_episode_action(cls, changes, episode, key, collection, action, properties=None):
        season_num, episode_num = key
        show = episode.show

        episodes = dict_path(changes, (
            collection, action, show.pk,
            'seasons', season_num,
            'episodes'
        ))

        episodes[episode_num] = properties
