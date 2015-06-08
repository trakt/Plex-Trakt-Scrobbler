from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.handlers.core import DataHandler, MediaHandler, bind

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, key, p_item, p_progress, t_progress):
        kwargs = {
            'key': key
        }

        # Retrieve plex parameters
        p_duration = p_item.get('part', {}).get('duration')

        if p_duration is None:
            # Missing data required for playback syncing
            return None

        kwargs['p_value'] = p_item.get('settings', {}).get('view_offset')

        # Set arguments for action
        if action in ['added', 'changed']:
            # Calculate trakt view offset
            t_value = p_duration * (float(t_progress) / 100)
            t_value = int(round(t_value, 0))

            kwargs['p_duration'] = p_duration
            kwargs['t_value'] = t_value

            if t_value <= 60 * 1000:
                # Ignore progress below one minute
                return None

        return kwargs

    @staticmethod
    def get_operands(p_item, t_item):
        # Retrieve plex parameters
        p_duration = p_item.get('part', {}).get('duration')
        p_view_offset = p_item.get('settings', {}).get('view_offset')

        # Calculate progress in plex (if available)
        p_progress = None

        if p_duration is not None and p_view_offset is not None:
            # Calculate progress from duration and view offset
            p_progress = round((float(p_view_offset) / p_duration) * 100, 2)

        # Retrieve trakt progress from item
        if type(t_item) is dict:
            t_progress = t_item.get('progress')
        else:
            t_progress = t_item.progress if t_item else None

        return p_progress, t_progress

    @staticmethod
    def update_progress(rating_key, time, duration):
        return Plex[':/timeline'].update(rating_key, 'stopped', time, duration)

    #
    # Modes
    #

    def fast_pull(self, action, rating_key, p_item, t_item):
        if not action:
            # No action provided
            return

        # Retrieve properties
        p_progress, t_progress = self.get_operands(p_item, t_item)

        # Execute action
        self.execute_action(action, (
            action,
            rating_key,
            p_item,
            p_progress,
            t_progress
        ))

    def pull(self, rating_key, p_item, t_item):
        # Retrieve properties
        p_progress, t_progress = self.get_operands(p_item, t_item)

        # Determine performed action
        action = self.get_action(p_progress, t_progress)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(action, (
            action,
            rating_key,
            p_item,
            p_progress,
            t_progress
        ))


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


class Playback(DataHandler):
    data = SyncData.Playback

    children = [
        Movies,
        Episodes
    ]
