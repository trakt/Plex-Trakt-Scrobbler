from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode, SyncActionMode
from plugin.sync.handlers.core import DataHandler, PullHandler, bind
from plugin.sync.handlers.playback.base import PlaybackHandler

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(PullHandler, PlaybackHandler):
    @classmethod
    def build_action(cls, action, p_item, p_value, t_value, **kwargs):
        data = {}

        # Retrieve plex parameters
        p_duration = p_item.get('part', {}).get('duration')

        if p_duration is None:
            # Missing data required for playback syncing
            return None

        p_settings = p_item.get('settings', {})
        p_view_count = p_settings.get('view_count', 0)

        if p_view_count > 0:
            # Ignore items that have been watched in plex
            return None

        data['p_duration'] = p_duration
        data['p_value'] = p_item.get('settings', {}).get('view_offset')

        # Set arguments for action
        if action in ['added', 'changed']:
            # Expand tuple, convert values to view offsets
            if type(t_value) is tuple:
                t_previous, t_current = t_value

                data['t_previous'] = cls.to_view_offset(p_duration, t_previous)
                data['t_value'] = cls.to_view_offset(p_duration, t_current)
            else:
                data['t_value'] = cls.to_view_offset(p_duration, t_value)

            # Ensure current value is available
            if data['t_value'] is None:
                # TODO Progress should be cleared on items during fast pulls
                return None

            # Ensure progress is above one minute
            if data['t_value'] <= 60 * 1000:
                return None

        # Set additional action attributes
        data.update(kwargs)

        return data

    @staticmethod
    def to_view_offset(duration, progress):
        if not progress:
            return None

        # Convert `progress` to a view offset
        view_offset = duration * (float(progress) / 100)

        # Round `view_offset` to an integer
        return int(round(view_offset, 0))

    def update_progress(self, key, time, duration):
        action_mode = self.configuration['sync.action.mode']

        if action_mode == SyncActionMode.Update:
            return Plex[':/timeline'].update(key, 'stopped', time, duration)

        if action_mode == SyncActionMode.Log:
            log.info('[%s] update_progress(%r)', key, time)
            return True

        raise NotImplementedError('Unable to update plex, action mode %r not supported', action_mode)

    #
    # Handlers
    #

    @bind('added')
    def on_added(self, key, p_duration, p_value, t_value, **kwargs):
        log.debug('%s.on_added(%s, %r, %r, %r)', self.media, key, p_duration, p_value, t_value)

        if p_value is not None and p_value > t_value:
            # Already updated progress
            return

        return self.update_progress(key, t_value, p_duration)

    @bind('changed')
    def on_changed(self, key, p_duration, p_value, t_value, **kwargs):
        log.debug('%s.on_changed(%s, %r, %r, %r)', self.media, key, p_duration, p_value, t_value)

        if p_value > t_value:
            # Ignore change, plex progress has advanced
            return

        return self.update_progress(key, t_value, p_duration)


class Movies(Base):
    media = SyncMedia.Movies


class Episodes(Base):
    media = SyncMedia.Episodes


class Pull(DataHandler):
    data = SyncData.Playback
    mode = [SyncMode.FastPull, SyncMode.Pull]

    children = [
        Movies,
        Episodes
    ]
