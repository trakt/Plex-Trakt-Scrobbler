from plugin.core.environment import Environment
from plugin.sync.core.enums import SyncMode, SyncMedia
from plugin.sync.modes.core.base import Mode

import json
import logging
import os

log = logging.getLogger(__name__)


class Base(Mode):
    mode = SyncMode.Push

    def __init__(self, task):
        super(Base, self).__init__(task)

    #
    # Execute handlers
    #

    def execute_movie(self, mo_id, pk, guid, p_item):
        # Execute handlers for each data type
        for data in self.get_data(SyncMedia.Movies):
            t_movie = self.trakt[(SyncMedia.Movies, data)].get(pk)

            self.execute_handlers(
                self.mode, SyncMedia.Movies, data,

                key=mo_id,

                guid=guid,
                p_item=p_item,

                t_item=t_movie
            )

    def execute_show(self, sh_id, pk, guid, p_show):
        for data in self.get_data(SyncMedia.Shows):
            t_show = self.trakt[(SyncMedia.Shows, data)].get(pk)

            # Execute show handlers
            self.execute_handlers(
                self.mode, SyncMedia.Shows, data,
                key=sh_id,
                guid=guid,

                p_item=p_show,

                t_item=t_show
            )

    def execute_episode(self, ep_id, pk, guid, identifier, p_show, p_season, p_episode):
        season_num, episode_num = identifier

        # Execute handlers for each data type
        for data in self.get_data(SyncMedia.Episodes):
            t_show, t_season, t_episode = self.t_objects(
                self.trakt[(SyncMedia.Episodes, data)], pk,
                season_num, episode_num
            )

            # Execute episode handlers
            self.execute_handlers(
                self.mode, SyncMedia.Episodes, data,

                key=ep_id,
                identifier=identifier,

                guid=guid,
                p_show=p_show,
                p_item=p_episode,

                t_show=t_show,
                t_item=t_episode
            )

    #
    # Helpers
    #

    @staticmethod
    def t_objects(collection, pk, season_num, episode_num):
        # Try find trakt `Show` from `collection`
        t_show = collection.get(pk)

        if t_show is None:
            return t_show, None, None

        # Try find trakt `Season`
        t_season = t_show.seasons.get(season_num)

        if t_season is None:
            return t_show, t_season, None

        # Try find trakt `Episode`
        t_episode = t_season.episodes.get(episode_num)

        return t_show, t_season, t_episode

    @classmethod
    def log_pending(cls, log, message, account, key, items):
        if type(items) is set:
            items = [
                (k, None)
                for k in items
            ]
        elif type(items) is dict:
            items = [
                (k, v)
                for k, v in items.items()
                if len(v) > 0
            ]
        else:
            raise ValueError('Unknown type for "pending" parameter')

        if len(items) < 1:
            return

        # Format items
        count, keys = cls.format_pending(items)

        # Update pending items report
        try:
            report_path = cls.write_pending(account, key, keys)
        except Exception as ex:
            log.warn('Unable to save report: %s', ex, exc_info=True)
            report_path = None

        # Display message in log file
        log.info(message, count, os.path.relpath(report_path, Environment.path.home))

    @classmethod
    def write_pending(cls, account, key, keys):
        directory = os.path.join(Environment.path.plugin_data, 'Reports', 'Sync', str(account.id), 'Pending')
        path = os.path.join(directory, '%s.json' % key)

        # Ensure directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Write items
        with open(path, 'w') as fp:
            json.dump(
                keys, fp,
                sort_keys=True,
                indent=4,
                separators=(',', ': ')
            )

        return path

    @classmethod
    def format_pending(cls, items):
        result = {}
        child_count = 0

        for key, children in items:
            key = '/'.join([str(k) for k in key])

            # Set show/movie
            result[key] = None

            if children is None:
                continue

            # Append keys of children
            result[key] = []

            for c_key in children:
                if type(c_key) is tuple and len(c_key) == 2:
                    c_key = 'S%02dE%02d' % c_key
                elif type(c_key) is tuple:
                    c_key = '/'.join([str(k) for k in c_key])

                result[key].append(c_key)
                child_count += 1

            # Sort children keys
            result[key] = sorted(result[key])

        if not child_count:
            return len(result), sorted(result.keys())

        return child_count, result
