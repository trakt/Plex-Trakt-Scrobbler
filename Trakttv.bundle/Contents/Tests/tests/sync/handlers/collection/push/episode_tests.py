from plugin.sync.core.enums import SyncMedia
from plugin.sync.handlers.collection.push import Push
from tests.sync.handlers.core.helpers import assert_added, assert_ignored, construct_handler

from datetime import datetime


def test_added_basic():
    episodes = construct_handler(Push, SyncMedia.Episodes)

    assert_added(
        episodes, 101,
        'tt100',

        identifier=(1, 1),
        p_show={
            'title': 'One',
            'year': 2000
        },
        p_item={
            'media': {}
        },
        p_value=datetime(2000, 6, 14),
        t_value=None,

        expected={
            'ids': {'imdb': 'tt100'},

            'seasons': {
                1: {
                    'number': 1,

                    'episodes': {
                        1: {
                            'number': 1,

                            'collected_at': '2000-06-14T00:00:00.000-00:00',
                            'media_type': 'digital',
                        }
                    }
                }
            }
        }
    )

    assert_added(
        episodes, 102,
        'tt200',

        identifier=(1, 2),
        p_show={
            'title': 'Two',
            'year': 2000
        },
        p_item={
            'media': {}
        },
        p_value=datetime(2000, 6, 14),
        t_value=None,

        expected={
            'ids': {'imdb': 'tt100'},

            'seasons': {
                1: {
                    'number': 1,

                    'episodes': {
                        2: {
                            'number': 2,

                            'collected_at': '2000-06-14T00:00:00.000-00:00',
                            'media_type': 'digital',
                        }
                    }
                }
            }
        }
    )


def test_added_metadata():
    episodes = construct_handler(Push, SyncMedia.Episodes)

    assert_added(
        episodes, 101,
        'tt100',

        identifier=(1, 1),
        p_show={
            'title': 'One',
            'year': 2000
        },
        p_item={
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
            'ids': {'imdb': 'tt100'},

            'seasons': {
                1: {
                    'number': 1,

                    'episodes': {
                        1: {
                            'number': 1,

                            'collected_at': '2000-06-14T00:00:00.000-00:00',
                            'media_type': 'digital',

                            'audio': 'mp3',
                            'audio_channels': '2.0',
                            'resolution': 'hd_1080p'
                        }
                    }
                }
            }
        }
    )

    assert_added(
        episodes, 102,
        'tt200',

        identifier=(1, 2),
        p_show={
            'title': 'Two',
            'year': 2000
        },
        p_item={
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
            'ids': {'imdb': 'tt100'},

            'seasons': {
                1: {
                    'number': 1,

                    'episodes': {
                        2: {
                            'number': 2,

                            'collected_at': '2000-06-14T00:00:00.000-00:00',
                            'media_type': 'digital',

                            'audio': 'dolby_digital',
                            'audio_channels': '5.1',
                            'resolution': 'sd_480i'
                        }
                    }
                }
            }
        }
    )


def test_existing():
    episodes = construct_handler(Push, SyncMedia.Episodes)

    assert_ignored(
        episodes, 101,
        'tt100',

        identifier=(1, 1),
        p_show={
            'title': 'One',
            'year': 2000
        },
        p_item={},
        p_value=datetime(2000, 6, 14),
        t_value=datetime(2000, 6, 14)
    )

    assert_ignored(
        episodes, 102,
        'tt100',

        identifier=(1, 2),
        p_show={
            'title': 'One',
            'year': 2000
        },
        p_item={},
        p_value=None,
        t_value=datetime(2000, 6, 14)
    )
