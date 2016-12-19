from tests.scrobbler.engine.core.helpers import assert_events

from plex_mock.models import Session
from plugin.scrobbler.core import SessionEngine


def test_simple():
    engine = SessionEngine()
    session = Session(rating_key=100, state='create', duration=50 * 1000, view_offset=0, part=1)

    # playing
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 1000, 'part': 1})], [('start',)])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 3000, 'part': 1})], [])

    # paused
    assert_events(engine, session, [('paused', {'rating_key': 100, 'view_offset': 3000, 'part': 1})], [('pause',)])
    assert_events(engine, session, [('paused', {'rating_key': 100, 'view_offset': 3000, 'part': 1})], [])

    # playing
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 4000, 'part': 1})], [('start',)])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 4000, 'part': 1})], [])

    # stopped
    assert_events(engine, session, [('stopped', {'rating_key': 100, 'view_offset': 5000, 'part': 1})], [('stop',)])
    assert_events(engine, session, [('stopped', {'rating_key': 100, 'view_offset': 5000, 'part': 1})], [])

    # media change
    assert_events(engine, session, [('playing', {'rating_key': 101, 'view_offset': 1000, 'part': 1})], [('start',)])


def test_finished():
    engine = SessionEngine()
    session = Session(rating_key=100, state='create', duration=50 * 1000, view_offset=0, part=1)

    # playing
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 1000, 'part': 1})], [('start',)])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 2000, 'part': 1})], [])

    # stopped
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 50 * 1000, 'part': 1})], [('stop',)])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 51 * 1000, 'part': 1})], [])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 52 * 1000, 'part': 1})], [])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 53 * 1000, 'part': 1})], [])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 54 * 1000, 'part': 1})], [])


def test_stopped():
    engine = SessionEngine()
    session = Session(rating_key=100, state='create', duration=50 * 1000, view_offset=0, part=1)

    # Start watching item
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset':  1000, 'part': 1})], [('start',)])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 10000, 'part': 1})], [])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 20000, 'part': 1})], [])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 30000, 'part': 1})], [])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 40000, 'part': 1})], [])

    # Ensure "stop" actions aren't duplicated
    assert_events(engine, session, [('stopped', {'rating_key': 100, 'view_offset': 50000, 'part': 1})], [('stop',)])
    assert_events(engine, session, [('paused',  {'rating_key': 100, 'view_offset': 50000, 'part': 1})], [])
    assert_events(engine, session, [('stopped', {'rating_key': 100, 'view_offset': 50000, 'part': 1})], [])

    # Ensure item can be restarted
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 10000, 'part': 1})], [('start',)])
    assert_events(engine, session, [('stopped', {'rating_key': 100, 'view_offset': 50000, 'part': 1})], [('stop',)])
