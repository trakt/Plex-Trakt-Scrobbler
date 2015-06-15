from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import DataHandler, bind
from plugin.sync.handlers.playback.base import PlaybackHandler

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(PlaybackHandler):
    @staticmethod
    def build_action(action, p_item, p_value, t_value, **kwargs):
        data = {}

        # Retrieve plex parameters
        p_duration = p_item.get('part', {}).get('duration')

        if p_duration is None:
            # Missing data required for playback syncing
            return None

        data['p_value'] = p_item.get('settings', {}).get('view_offset')

        # Set arguments for action
        if action in ['added', 'changed']:
            # Calculate trakt view offset
            t_value = p_duration * (float(t_value) / 100)
            t_value = int(round(t_value, 0))

            data['p_duration'] = p_duration
            data['t_value'] = t_value

            if t_value <= 60 * 1000:
                # Ignore progress below one minute
                return None

        data.update(kwargs)
        return data

    @staticmethod
    def update_progress(rating_key, time, duration):
        return Plex[':/timeline'].update(rating_key, 'stopped', time, duration)

    #
    # Modes
    #

    def fast_pull(self, action, p_item, t_item, **kwargs):
        if not action:
            # No action provided
            return

        # Retrieve properties
        p_progress, t_progress = self.get_operands(p_item, t_item)

        # Execute action
        self.execute_action(
            action,

            p_item=p_item,
            p_value=p_progress,
            t_value=t_progress,
            **kwargs
        )

    def pull(self, p_item, t_item, **kwargs):
        # Retrieve properties
        p_progress, t_progress = self.get_operands(p_item, t_item)

        # Determine performed action
        action = self.get_action(p_progress, t_progress)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(
            action,

            p_item=p_item,
            p_value=p_progress,
            t_value=t_progress,
            **kwargs
        )


class Movies(Base):
    media = SyncMedia.Movies

    @bind('added')
    def on_added(self, key, p_duration, p_value, t_value):
        log.debug('Movies.on_added(%s, %r, %r, %r)', key, p_duration, p_value, t_value)

        if p_value is not None and p_value > t_value:
            # Already updated progress
            return

        return self.update_progress(key, t_value, p_duration)

    @bind('changed')
    def on_changed(self, key, p_duration, p_value, t_value):
        log.debug('Movies.on_changed(%s, %r, %r, %r)', key, p_duration, p_value, t_value)

        if p_value > t_value:
            # Ignore change, plex progress has advanced
            return

        return self.update_progress(key, t_value, p_duration)


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added')
    def on_added(self, key, p_duration, p_value, t_value):
        log.debug('Episodes.on_added(%s, %r, %r, %r)', key, p_duration, p_value, t_value)

        if p_value is not None and p_value > t_value:
            # Already updated progress
            return

        return self.update_progress(key, t_value, p_duration)

    @bind('changed')
    def on_changed(self, key, p_duration, p_value, t_value):
        log.debug('Episodes.on_changed(%s, %r, %r, %r)', key, p_duration, p_value, t_value)

        if p_value > t_value:
            # Ignore change, plex progress has advanced
            return

        return self.update_progress(key, t_value, p_duration)


class Pull(DataHandler):
    data = SyncData.Playback
    mode = [SyncMode.FastPull, SyncMode.Pull]

    children = [
        Movies,
        Episodes
    ]
