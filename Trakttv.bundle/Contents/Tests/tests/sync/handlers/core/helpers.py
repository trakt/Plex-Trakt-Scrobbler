from plugin.core.helpers.variable import dict_path
from plugin.sync.core.enums import SyncData, SyncMedia, SyncMode
from plugin.sync.core.task import SyncTask
from plugin.sync.main import Main

from plex_metadata import Guid
import pytest


def construct_handler(handler_cls, media):
    task = SyncTask(None, SyncMode.Full, handler_cls.data, media, None, None)

    main = Main()
    main.current = task

    # Construct data handler
    handler = handler_cls(task)

    # Construct media handler
    for cls in handler.children:
        if cls.media == media:
            return cls(handler, task)

    raise ValueError("Unknown media type: %r", media)


def get_artifact_key(handler):
    if handler.media == SyncMedia.Movies:
        return 'movies'

    if handler.media in [SyncMedia.Shows, SyncMedia.Seasons, SyncMedia.Episodes]:
        return 'shows'

    raise ValueError('Unknown media: %r', handler.media)


def assert_added(handler, key, sid, expected, **kwargs):
    __tracebackhide__ = True

    # Determine media type
    artifact_key = get_artifact_key(handler)

    # Set default attributes
    if expected:
        expected['ids'] = {'imdb': sid}

    # Add item
    handler.on_added(key, Guid.parse('com.plexapp.agents.imdb://%s' % sid), **kwargs)

    # Ensure item was added
    item = dict_path(handler.current.artifacts.artifacts, [
        SyncData.Collection, 'add', artifact_key,
        ('imdb', sid)
    ])

    if item != expected:
        pytest.fail("Artifact %r doesn't match the expected item %r" % (item, expected))


def assert_ignored(handler, key, sid, **kwargs):
    __tracebackhide__ = True

    # Determine media type
    artifact_key = get_artifact_key(handler)

    # Add item
    handler.on_added(key, Guid.parse('com.plexapp.agents.imdb://%s' % sid), **kwargs)

    # Ensure item wasn't added
    item = dict_path(handler.current.artifacts.artifacts, [
        SyncData.Collection, 'add', artifact_key,
        ('imdb', sid)
    ])

    if item != {}:
        pytest.fail("Artifact found, expected the item to be ignored")
