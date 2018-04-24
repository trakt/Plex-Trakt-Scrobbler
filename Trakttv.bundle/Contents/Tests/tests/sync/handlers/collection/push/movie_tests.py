from plugin.sync.core.enums import SyncMedia
from plugin.sync.handlers.collection.push import Push
from tests.sync.handlers.core.helpers import assert_added, assert_ignored, construct_handler

from datetime import datetime


def test_added_basic():
    movies = construct_handler(Push, SyncMedia.Movies)

    assert_added(
        movies, 100,
        'tt100',

        p_item={
            'title': 'One',
            'year': 2000,
        },
        p_value=datetime(2000, 6, 14),
        t_value=None,

        expected={
            'collected_at': '2000-06-14T00:00:00.000-00:00',
            'media_type': 'digital'
        }
    )

    assert_added(
        movies, 200,
        'tt200',

        p_item={
            'title': 'Two',
            'year': 2000,
        },
        p_value=datetime(2000, 6, 21),
        t_value=None,

        expected={
            'collected_at': '2000-06-21T00:00:00.000-00:00',
            'media_type': 'digital'
        }
    )


def test_added_metadata():
    movies = construct_handler(Push, SyncMedia.Movies)

    assert_added(
        movies, 100,
        'tt100',

        p_item={
            'title': 'One',
            'year': 2000,

            'media': {
                'audio_codec': 'mp3',
                'audio_channels': 2.0,

                'width': 1920,
                'interlaced': False
            }
        },
        p_value=datetime(2000, 6, 14),
        t_value=None,

        expected={
            'collected_at': '2000-06-14T00:00:00.000-00:00',
            'media_type': 'digital',

            'audio': 'mp3',
            'audio_channels': '2.0',
            'resolution': 'hd_1080p'
        }
    )

    assert_added(
        movies, 200,
        'tt200',

        p_item={
            'title': 'Two',
            'year': 2000,

            'media': {
                'audio_codec': 'ac3',
                'audio_channels': 6.0,

                'width': 720,
                'interlaced': True
            }
        },
        p_value=datetime(2000, 6, 14),
        t_value=None,

        expected={
            'collected_at': '2000-06-14T00:00:00.000-00:00',
            'media_type': 'digital',

            'audio': 'dolby_digital',
            'audio_channels': '5.1',
            'resolution': 'sd_480i'
        }
    )


def test_existing():
    movies = construct_handler(Push, SyncMedia.Movies)

    assert_ignored(
        movies, 100,
        'tt100',

        p_item={
            'title': 'One',
            'year': 2000
        },
        p_value=datetime(2000, 6, 14),
        t_value=datetime(2000, 6, 14)
    )

    assert_ignored(
        movies, 200,
        'tt200',

        p_item={
            'title': 'Two',
            'year': 2000
        },
        p_value=None,
        t_value=datetime(2000, 6, 14)
    )
