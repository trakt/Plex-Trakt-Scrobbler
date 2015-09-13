from plugin.core.identifier import Identifier

from plex_metadata import Guid
import pytest


def test_empty():
    assert Identifier.get_ids(None) == {}


def test_unknown():
    assert Identifier.get_ids(Guid('example', '123456', None), strict=False) == {}


def test_unknown_strict():
    assert Identifier.get_ids(Guid('example', '123456', None), strict=True) is None


def test_string():
    assert Identifier.get_ids('imdb://123456') == {'imdb': '123456'}


def test_imdb():
    assert Identifier.get_ids(Guid('imdb', '123456', None)) == {'imdb': '123456'}


def test_tmdb():
    assert Identifier.get_ids(Guid('tmdb', '123456', None)) == {'tmdb': 123456}
    assert Identifier.get_ids(Guid('tmdb', 123456, None)) == {'tmdb': 123456}


def test_tvdb():
    assert Identifier.get_ids(Guid('tvdb', '123456', None)) == {'tvdb': 123456}
    assert Identifier.get_ids(Guid('tvdb', 123456, None)) == {'tvdb': 123456}
