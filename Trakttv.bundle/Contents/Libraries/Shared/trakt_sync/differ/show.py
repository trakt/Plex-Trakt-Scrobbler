from trakt_sync.differ.core.base import Differ
from trakt_sync.differ.core.helpers import dict_path
from trakt_sync.differ.core.result import Result
from trakt_sync.differ.handlers import Collection, Playback, Ratings, Watched


class ShowDiffer(Differ):
    def __init__(self):
        self.season = SeasonDiffer()

        self.handlers = [
            h(self) for h in [
                Ratings
            ]
        ]

    def run(self, base, current, handlers=None):
        keys_base = set(base.keys())
        keys_current = set(current.keys())

        result = ShowResult()

        for key in keys_current - keys_base:
            actions = self.process_added(current[key], handlers=handlers)

            self.store_actions(result, actions)

        for key in keys_base - keys_current:
            actions = self.process_removed(base[key], handlers=handlers)

            self.store_actions(result, actions)

        for key in keys_base & keys_current:
            actions = self.process_common(base[key], current[key], handlers=handlers)

            self.store_actions(result, actions)

        # Run season differ on shows
        for key in keys_base | keys_current:
            b = base.get(key)
            c = current.get(key)

            self.season.run(
                b.seasons if b else {},
                c.seasons if c else {},
                result=result,
                handlers=handlers
            )

        return result

    @staticmethod
    def store_action(result, keys, collection, action, properties=None):
        Differ.store_action(result, keys, collection, action, properties)

        # Update show metrics
        Differ.increment_metric(result.metrics.shows, collection, action)


class SeasonDiffer(Differ):
    def __init__(self):
        self.episode = EpisodeDiffer()

        self.handlers = [
            h(self) for h in [
                Ratings
            ]
        ]

    def run(self, base, current, result=None, handlers=None):
        keys_base = set(base.keys())
        keys_current = set(current.keys())

        if result is None:
            result = ShowResult()

        for key in keys_current - keys_base:
            actions = self.process_added(current[key], handlers=handlers)

            self.store_season_actions(result, current[key], actions)

        for key in keys_base - keys_current:
            actions = self.process_removed(base[key], handlers=handlers)

            self.store_season_actions(result, base[key], actions)

        for key in keys_base & keys_current:
            actions = self.process_common(base[key], current[key], handlers=handlers)

            self.store_season_actions(result, current[key], actions)

        # Run episode differ on seasons
        for key in keys_base | keys_current:
            b = base.get(key)
            c = current.get(key)

            self.episode.run(
                b.episodes if b else {},
                c.episodes if c else {},
                result=result,
                handlers=handlers
            )

        return result

    @classmethod
    def store_season_actions(cls, result, season, actions):
        for action in actions:
            cls.store_season_action(result, season, *action)

    @classmethod
    def store_season_action(cls, result, season, key, collection, action, properties=None):
        show = season.show

        # Store action in `result`
        seasons = dict_path(result.changes, (
            collection, action,
            list(cls.item_keys(show)),
            'seasons',
        ))

        seasons[key] = properties

        # Update episode metrics
        Differ.increment_metric(result.metrics.seasons, collection, action)


class EpisodeDiffer(Differ):
    def __init__(self):
        self.handlers = [
            h(self) for h in [
                Collection,
                Playback,
                Ratings,
                Watched
            ]
        ]

    def run(self, base, current, result=None, handlers=None):
        keys_base = set(base.keys())
        keys_current = set(current.keys())

        if result is None:
            result = ShowResult()

        for key in keys_current - keys_base:
            actions = self.process_added(current[key], handlers=handlers)

            self.store_episode_actions(result, current[key], actions)

        for key in keys_base - keys_current:
            actions = self.process_removed(base[key], handlers=handlers)

            self.store_episode_actions(result, base[key], actions)

        for key in keys_base & keys_current:
            actions = self.process_common(base[key], current[key], handlers=handlers)

            self.store_episode_actions(result, current[key], actions)

        return result

    @classmethod
    def store_episode_actions(cls, result, episode, actions):
        for action in actions:
            cls.store_episode_action(result, episode, *action)

    @classmethod
    def store_episode_action(cls, result, episode, key, collection, action, properties=None):
        season_num, episode_num = key[0]
        show = episode.show

        # Store action in `result`
        episodes = dict_path(result.changes, (
            collection, action,
            list(cls.item_keys(show)),
            'seasons', season_num,
            'episodes'
        ))

        episodes[episode_num] = properties

        # Update episode metrics
        Differ.increment_metric(result.metrics.episodes, collection, action)


class ShowResult(Result):
    def __init__(self):
        super(ShowResult, self).__init__()

        self.metrics = ShowMetrics()


class ShowMetrics(object):
    def __init__(self):
        self.shows = {}
        self.seasons = {}
        self.episodes = {}
