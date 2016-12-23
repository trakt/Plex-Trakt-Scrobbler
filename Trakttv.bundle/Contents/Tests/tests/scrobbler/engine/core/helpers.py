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
