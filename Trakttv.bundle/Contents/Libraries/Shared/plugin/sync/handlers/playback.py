from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.handlers.core import DataHandler, MediaHandler, bind

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, rating_key, p_item, p_progress, t_progress):
        kwargs = {
            'rating_key': rating_key
        }

        # Retrieve plex parameters
        p_duration = p_item.get('duration')

        if p_duration is None:
            # Missing data required for playback syncing
            return None

        p_view_offset = p_item.get('settings', {}).get('view_offset')

        # Set arguments for action
        if action in ['added', 'changed']:
            # Calculate trakt view offset
            t_view_offset = p_duration * (float(t_progress) / 100)
            t_view_offset = int(round(t_view_offset, 0))

            kwargs['p_duration'] = p_duration
            kwargs['t_view_offset'] = t_view_offset

            if t_view_offset <= 60 * 1000:
                # Ignore progress below one minute
                return None

        if action == 'changed':
            kwargs['p_view_offset'] = p_view_offset

        return kwargs

    @staticmethod
    def get_operands(p_item, t_item):
        # Retrieve plex parameters
        p_duration = p_item.get('duration')
        p_view_offset = p_item.get('settings', {}).get('view_offset')

        # Calculate progress in plex (if available)
        p_progress = None

        if p_duration is not None and p_view_offset is not None:
            # Calculate progress from duration and view offset
            p_progress = round((float(p_view_offset) / p_duration) * 100, 2)

        return (
            p_progress,
            t_item.progress if t_item else None
        )

    @staticmethod
    def update_progress(rating_key, time, duration):
        return Plex[':/timeline'].update(rating_key, 'stopped', time, duration)

    #
    # Modes
    #

    def fast_pull(self, action, rating_key, p_item, t_item):
        log.debug('fast_pull(%r, %r, %r, %r)', action, rating_key, p_item, t_item)

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
    def on_added(self, rating_key, t_view_offset, p_duration):
        log.debug('Movies.on_added(%s, %r, %r)', rating_key, t_view_offset, p_duration)

        return self.update_progress(rating_key, t_view_offset, p_duration)

    @bind('changed')
    def on_changed(self, rating_key, t_view_offset, p_view_offset, p_duration):
        log.debug('Movies.on_changed(%s, %r, %r, %r)', rating_key, t_view_offset, p_view_offset, p_duration)

        if t_view_offset < p_view_offset:
            # Ignore change, plex progress has advanced
            return

        return self.update_progress(rating_key, t_view_offset, p_duration)


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added')
    def on_added(self, rating_key, t_view_offset, p_duration):
        log.debug('Episodes.on_added(%s, %r, %r)', rating_key, t_view_offset, p_duration)

        return self.update_progress(rating_key, t_view_offset, p_duration)

    @bind('changed')
    def on_changed(self, rating_key, t_view_offset, p_view_offset, p_duration):
        log.debug('Episodes.on_changed(%s, %r, %r, %r)', rating_key, t_view_offset, p_view_offset, p_duration)

        if t_view_offset < p_view_offset:
            # Ignore change, plex progress has advanced
            return

        return self.update_progress(rating_key, t_view_offset, p_duration)


class Playback(DataHandler):
    data = SyncData.Playback

    children = [
        Movies,
        Episodes
    ]
