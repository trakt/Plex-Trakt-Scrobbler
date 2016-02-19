from plugin.core.identifier import Identifier

from plex_metadata import Guid
import pytest


def test_empty():
    assert Identifier.get_ids(None) == {}


def test_unknown():
    assert Identifier.get_ids(Guid.parse('example://123456'), strict=False) == {}


def test_unknown_strict():
    assert Identifier.get_ids(Guid.parse('example://123456'), strict=True) is None


def test_string():
    assert Identifier.get_ids('com.plexapp.agents.imdb://tt123456') == {'imdb': 'tt123456'}


def test_imdb():
    assert Identifier.get_ids(Guid.parse('com.plexapp.agents.imdb://tt123456')) == {'imdb': 'tt123456'}


def test_tmdb():
    assert Identifier.get_ids(Guid.parse('com.plexapp.agents.themoviedb://123456')) == {'tmdb': 123456}
    assert Identifier.get_ids(Guid.parse('com.plexapp.agents.themoviedb://123456')) == {'tmdb': 123456}


def test_tvdb():
    assert Identifier.get_ids(Guid.parse('com.plexapp.agents.thetvdb://123456')) == {'tvdb': 123456}
    assert Identifier.get_ids(Guid.parse('com.plexapp.agents.thetvdb://123456')) == {'tvdb': 123456}
