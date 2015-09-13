from plugin.sync.handlers.collection.push import Base


def test_audio_channels():
    assert Base.get_audio_channels(None) is None

    assert Base.get_audio_channels(2) == '2.0'
    assert Base.get_audio_channels(3) == '2.1'
    assert Base.get_audio_channels(4) == '3.1'
    assert Base.get_audio_channels(5) == '4.1'
    assert Base.get_audio_channels(6) == '5.1'


def test_audio_codec():
    assert Base.get_audio_codec(None) is None
    assert Base.get_audio_codec('INVALID_CODEC') is None

    assert Base.get_audio_codec('mp3') == 'mp3'
    assert Base.get_audio_codec('dca')


def test_resolution():
    assert Base.get_resolution(480, False) == 'sd_480p'
    assert Base.get_resolution(480, True) == 'sd_480i'

    assert Base.get_resolution(576, False) == 'sd_576p'
    assert Base.get_resolution(576, True) == 'sd_576i'

    assert Base.get_resolution(720, False) == 'hd_720p'
    assert Base.get_resolution(720, True) == 'hd_720p'

    assert Base.get_resolution(1080, False) == 'hd_1080p'
    assert Base.get_resolution(1080, True) == 'hd_1080i'

    assert Base.get_resolution(2160, False) == 'uhd_4k'
    assert Base.get_resolution(2160, True) == 'uhd_4k'


def test_metadata_missing():
    assert Base.build_metadata({
        'media': {
            'audio_codec': 'INVALID_CODEC'
        }
    }) == {
        'media_type': 'digital'
    }
