from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.core import bind
from plugin.sync.handlers.core.base import DataHandler, MediaHandler

import logging
import re

log = logging.getLogger(__name__)

AUDIO_CODECS = {
    'lpcm':             'pcm',
    'mp3':              None,
    'aac':              None,
    'ogg':              'vorbis',
    'wma':              None,

    'dts':              '(dca|dta)',
    'dts_ma':           'dtsma',

    'dolby_prologic':   'dolby.?pro',
    'dolby_digital':    'ac.?3',
    'dolby_truehd':     'truehd'
}

# compile patterns in `AUDIO_CODECS`
for k, v in AUDIO_CODECS.items():
    if v is None:
        continue

    try:
        AUDIO_CODECS[k] = re.compile(v, re.IGNORECASE)
    except Exception:
        log.warn('Unable to compile regex pattern: %r', v, exc_info=True)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, p_guid, p_item, p_value, **kwargs):
        data = {}

        if action in ['added', 'changed']:
            data['p_guid'] = p_guid
            data['p_item'] = p_item

            data['p_value'] = p_value

        data.update(kwargs)
        return data

    @staticmethod
    def get_operands(p_item, t_item):
        p_added_at = p_item.get('added_at')

        # Retrieve trakt `viewed_at` from item
        if type(t_item) is dict:
            t_added_at = t_item.get('collected_at')
        else:
            t_added_at = t_item.collected_at if t_item else None

        return p_added_at, t_added_at

    def get_action(self, p_value, t_value):
        if p_value is None and t_value is not None:
            return 'removed'

        if p_value is not None and t_value is None:
            return 'added'

        if p_value != t_value:
            return 'changed'

        return None

    @staticmethod
    def get_audio_channels(channels):
        if channels < 3:
            return '%.01f' % channels

        return '%.01f' % (channels - 0.9)

    @staticmethod
    def get_audio_codec(codec):
        for key, regex in AUDIO_CODECS.items():
            if key == codec:
                return key

            if regex and regex.match(codec):
                return key

        return None

    @staticmethod
    def get_resolution(height, interlaced):
        # 4k
        if height > 1100:
            return 'uhd_4k'

        # 1080
        if height > 720:
            if interlaced:
                return 'hd_1080i'
            else:
                return 'hd_1080p'

        # 720
        if height > 576:
            return 'hd_720p'

        # 576
        if height > 480:
            if interlaced:
                return 'sd_576i'
            else:
                return 'sd_576p'

        # 480
        if interlaced:
            return 'sd_480i'

        return 'sd_480p'

    @classmethod
    def build_metadata(cls, p_item):
        p_media = p_item.get('media', {})

        data = {}

        # Set attributes
        if 'audio_codec' in p_media:
            data['audio'] = cls.get_audio_codec(p_media['audio_codec'])

        if 'audio_channels' in p_media:
            data['audio_channels'] = cls.get_audio_channels(p_media['audio_channels'])

        if 'height' in p_media and 'interlaced' in p_media:
            data['resolution'] = cls.get_resolution(p_media['height'], p_media['interlaced'])

        # Remove any invalid/missing attributes
        for key in data.keys():
            if data.get(key) is None:
                del data[key]

        return data

    def push(self, p_item, t_item, **kwargs):
        # Retrieve properties
        p_added_at, t_added_at = self.get_operands(p_item, t_item)

        # Determine performed action
        action = self.get_action(p_added_at, t_added_at)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(
            action,

            p_item=p_item,
            p_value=p_added_at,
            t_value=t_added_at,
            **kwargs
        )


class Movies(Base):
    media = SyncMedia.Movies


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added', [SyncMode.Push])
    def on_added(self, key, p_guid, identifier, p_show, p_item, p_value, t_value, **kwargs):
        log.debug('Episodes.on_added(%r, ...)', key)

        if t_value:
            return

        self.store_episode('add', p_guid,
            identifier, p_show,
            collected_at=p_value,
            **self.build_metadata(p_item)
        )


class Push(DataHandler):
    data = SyncData.Collection
    mode = SyncMode.Push

    children = [
        Movies,
        Episodes
    ]
