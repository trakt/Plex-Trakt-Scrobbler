from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.handlers.collection.base import CollectionHandler
from plugin.sync.handlers.core import DataHandler, PushHandler, bind

import logging
import re

log = logging.getLogger(__name__)

AUDIO_CODECS = {
    'lpcm':                 'pcm',
    'mp3':                  None,
    'aac':                  None,
    'ogg':                  'vorbis',
    'wma':                  None,

    'dts':                  '(dca|dta)',
    'dts_ma':               'dtsma',

    'dolby_prologic':       'dolby.?pro',
    'dolby_digital':        'ac.?3',
    'dolby_digital_plus':   'eac.?3',
    'dolby_truehd':         'truehd'
}

# compile patterns in `AUDIO_CODECS`
for k, v in AUDIO_CODECS.items():
    if v is None:
        continue

    try:
        AUDIO_CODECS[k] = re.compile(v, re.IGNORECASE)
    except Exception:
        log.warn('Unable to compile regex pattern: %r', v, exc_info=True)


class Base(PushHandler, CollectionHandler):
    @staticmethod
    def get_audio_channels(channels):
        if channels is None:
            return None

        if channels < 3:
            return '%.01f' % channels

        return '%.01f' % (channels - 0.9)

    @staticmethod
    def get_audio_codec(codec):
        if codec is None:
            return None

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

        data = {
            'media_type': 'digital'
        }

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


class Movies(Base):
    media = SyncMedia.Movies

    @bind('added', [SyncMode.Full, SyncMode.Push])
    def on_added(self, key, guid, p_item, p_value, t_value, **kwargs):
        log.debug('Movies.on_added(%r, ...)', key)

        if t_value:
            return

        self.store_movie('add', guid,
            key, p_item,
            collected_at=p_value,
            **self.build_metadata(p_item)
        )

    @bind('removed', [SyncMode.Full])
    def on_removed(self, guid, **kwargs):
        if not self.configuration['sync.collection.clean'] or self.current.kwargs.get('section'):
            # Collection cleaning hasn't been enabled
            return

        log.debug('Movies.on_removed(%r) - %r', guid, kwargs)

        # Store action in artifacts
        self.store_movie('remove', guid)


class Episodes(Base):
    media = SyncMedia.Episodes

    @bind('added', [SyncMode.Full, SyncMode.Push])
    def on_added(self, key, guid, identifier, p_show, p_item, p_value, t_value, **kwargs):
        log.debug('Episodes.on_added(%r, ...)', key)

        if t_value:
            return

        self.store_episode('add', guid,
            identifier, key,
            p_show, p_item,
            collected_at=p_value,
            **self.build_metadata(p_item)
        )

    @bind('removed', [SyncMode.Full])
    def on_removed(self, guid, identifier, **kwargs):
        if not self.configuration['sync.collection.clean'] or self.current.kwargs.get('section'):
            # Collection cleaning hasn't been enabled
            return

        log.debug('Episodes.on_removed(%r) - %r', guid, kwargs)

        # Store action in artifacts
        self.store_episode('remove', guid, identifier)


class Push(DataHandler):
    data = SyncData.Collection
    mode = SyncMode.Push

    children = [
        Movies,
        Episodes
    ]
