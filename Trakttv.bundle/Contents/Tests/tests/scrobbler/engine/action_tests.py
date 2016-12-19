from tests.scrobbler.engine.core.helpers import assert_events

from plex_mock.models import Session
from plugin.scrobbler.core import SessionEngine


def test_stopped():
    engine = SessionEngine()
    session = Session(rating_key=100, state='create', duration=50 * 1000, view_offset=0, part=1)

    # playing
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 1 * 1000, 'part': 1})], [('start',)])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 3 * 1000, 'part': 1})], [])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 5 * 1000, 'part': 1})], [])

    # finished
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 50 * 1000, 'part': 1})], [('stop',)])

    # stopped
    assert_events(engine, session, [('stopped', {'rating_key': 100, 'view_offset': 50 * 1000, 'part': 1})], [])


def test_paused():
    engine = SessionEngine()
    session = Session(rating_key=100, state='create', duration=50 * 1000, view_offset=0, part=1)

    # playing
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 1 * 1000, 'part': 1})], [('start',)])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 3 * 1000, 'part': 1})], [])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 5 * 1000, 'part': 1})], [])

    # paused
    assert_events(engine, session, [('paused', {'rating_key': 100, 'view_offset': 37 * 1000, 'part': 1})], [('pause',)])

    # playing
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 38 * 1000, 'part': 1})], [('start',)])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 39 * 1000, 'part': 1})], [])

    # paused
    assert_events(engine, session, [('paused', {'rating_key': 100, 'view_offset': 40 * 1000, 'part': 1})], [('pause',)])

    # finished
    assert_events(engine, session, [('paused', {'rating_key': 100, 'view_offset': 49 * 1000, 'part': 1})], [('stop',)])
    assert_events(engine, session, [('paused', {'rating_key': 100, 'view_offset': 50 * 1000, 'part': 1})], [])

    # stopped
    assert_events(engine, session, [('stopped', {'rating_key': 100, 'view_offset': 50 * 1000, 'part': 1})], [])


def test_unplayed():
    engine = SessionEngine()
    session = Session(rating_key=100, state='create', duration=50 * 1000, view_offset=0, part=1)

    assert_events(engine, session, [('paused', {'rating_key': 100, 'view_offset': 50000, 'part': 1})], [])
    assert_events(engine, session, [('stopped', {'rating_key': 100, 'view_offset': 50000, 'part': 1})], [])
