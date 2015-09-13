from plugin.core.helpers.variable import *

import pytest


def test_dict_path():
    d = {
        'one': {'two': 2}
    }

    # Exists
    assert dict_path(d, ['one']) == {'two': 2}
    assert dict_path(d, ['one', 'two']) is 2

    # Invalid
    assert dict_path(d, ['invalid']) == {}
    assert dict_path(d, ['one', 'invalid']) == {}

    # Invalid type
    with pytest.raises(ValueError):
        dict_path(d, 'test')


def test_flatten():
    assert flatten(None) is None
    assert flatten('One (Two), Three') == 'one two three'


def test_merge():
    # Basic merge
    assert merge({
        'one': 1,
        'two': 2,

        'd': {
            'one': 1,
            'two': 2
        }
    }, {
        'two': 'two',
        'three': 3,

        'd': {
            'two': 'two',
            'three': 3
        }
    }) == {
        'one': 1,
        'two': 'two',
        'three': 3,

        'd': {
            'two': 'two',
            'three': 3
        }
    }

    # Recursive merge
    assert merge({
        'one': 1,
        'two': 2,

        'd': {
            'one': 1,
            'two': 2
        }
    }, {
        'two': 'two',
        'three': 3,

        'd': {
            'two': 'two',
            'three': 3
        }
    }, recursive=True) == {
        'one': 1,
        'two': 'two',
        'three': 3,

        'd': {
            'one': 1,
            'two': 'two',
            'three': 3
        }
    }


def test_normalize():
    assert normalize(None) is None
    assert normalize(u'\u016A') == 'U'

    assert normalize('U') == 'U'


def test_resolve():
    assert resolve('test') == 'test'

    assert resolve(lambda: 'test') == 'test'


def test_to_integer():
    assert to_integer(None) == None

    assert to_integer(1) == 1
    assert to_integer('1') == 1

    assert to_integer('test') == None


def test_to_tuple():
    assert to_tuple(None) == (None,)

    assert to_tuple((1, 2)) == (1, 2)
    assert to_tuple(1) == (1,)


def test_try_convert():
    assert try_convert('1', int) == 1
    assert try_convert('test', int) == None

    assert try_convert(None, int) == None
