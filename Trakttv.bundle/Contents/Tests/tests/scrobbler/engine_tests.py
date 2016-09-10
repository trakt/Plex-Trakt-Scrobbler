from plex_mock.models import Session
from plugin.scrobbler.core import SessionEngine

import pytest


def transform_expected(events, expected):
    c_events = len(events)
    c_expected = len(expected)

    for x in xrange(max(c_events, c_expected)):
        key, payload = events[x] if x < c_events else (None, None)

        ex = expected[x] if x < c_expected else None

        if ex is None:
            continue

        if len(ex) == 1:
            key, = ex
        elif len(ex) == 2:
            key, payload = ex
        else:
            raise ValueError('Provided an unknown expected item: %r', ex)

        yield key, payload


def assert_events(engine, session, events, expected):
    __tracebackhide__ = True

    expected = list(transform_expected(events, expected))

    actions = list(engine.process(session, events))

    if actions != expected:
        pytest.fail("Returned actions %r doesn't match the expected actions %r" % (actions, expected))


def test_event_duplication():
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


def test_finished_duplication():
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


def test_stopped_duplication():
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


def test_finished():
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


def test_media_changed():
    engine = SessionEngine()
    session = Session(rating_key=100, state='create', duration=50 * 1000, view_offset=0, part=1)

    # playing
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 1 * 1000, 'part': 1})], [('start',)])
    assert_events(engine, session, [('playing', {'rating_key': 100, 'view_offset': 3 * 1000, 'part': 1})], [])

    assert_events(engine, session, [('playing', {'rating_key': 101, 'view_offset': 1 * 1000, 'part': 1})], [
        ('stop',  {'rating_key': 100, 'view_offset': 3 * 1000, 'part': 1}),
        ('start', {'rating_key': 101, 'view_offset': 1 * 1000, 'part': 1})
    ])


def test_media_changed_unplayed():
    engine = SessionEngine()
    session = Session(rating_key=100, state='create', duration=50 * 1000, view_offset=0, part=1)

    assert_events(engine, session, [('paused', {'rating_key': 100, 'view_offset': 50000, 'part': 1})], [])
    assert_events(engine, session, [('playing', {'rating_key': 101, 'view_offset': 0, 'part': 1})], [('start',)])


def test_unplayed():
    engine = SessionEngine()
    session = Session(rating_key=100, state='create', duration=50 * 1000, view_offset=0, part=1)

    assert_events(engine, session, [('paused', {'rating_key': 100, 'view_offset': 50000, 'part': 1})], [])
    assert_events(engine, session, [('stopped', {'rating_key': 100, 'view_offset': 50000, 'part': 1})], [])
