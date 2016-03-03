from tests.helpers import read

from plugin.sync.core.playlist.mapper import PlaylistMapper
from plugin.sync.core.task import SyncTask

from plex import Plex
from trakt import Trakt
import logging
import responses

log = logging.getLogger(__name__)

# Set client configuration defaults
Plex.configuration.defaults.server(host='mock')
Trakt.base_url = 'http://mock'


@responses.activate
def test_basic():
    # Setup response fixtures
    responses.add(
        responses.GET, 'http://mock:32400/library/metadata/101/allLeaves',
        body=read(__file__, "fixtures/plex/library/metadata/101/allLeaves.xml"), status=200,
        content_type='application/xml'
    )

    responses.add(
        responses.GET, 'http://mock:32400/library/metadata/106/children',
        body=read(__file__, "fixtures/plex/library/metadata/106/children.xml"), status=200,
        content_type='application/xml'
    )

    responses.add(
        responses.GET, 'http://mock:32400/library/metadata/107/children',
        body=read(__file__, "fixtures/plex/library/metadata/107/children.xml"), status=200,
        content_type='application/xml'
    )

    responses.add(
        responses.GET, 'http://mock:32400/playlists/1',
        body=read(__file__, "fixtures/plex/playlists/1.xml"), status=200,
        content_type='application/xml'
    )

    responses.add(
        responses.GET, 'http://mock:32400/playlists/1/items',
        body=read(__file__, "fixtures/plex/playlists/1/items.xml"), status=200,
        content_type='application/xml'
    )

    responses.add(
        responses.GET, 'http://mock/users/one/lists/mixed',
        body=read(__file__, "fixtures/trakt/users/one/lists/mixed.json"), status=200,
        content_type='application/json'
    )

    responses.add(
        responses.GET, 'http://mock/users/one/lists/1413325/items',
        body=read(__file__, "fixtures/trakt/users/one/lists/mixed/items.json"), status=200,
        content_type='application/json'
    )

    # Build task
    task = SyncTask(
        account=None,

        mode=None,
        data=None,
        media=None,

        result=None,
        status=None
    )

    # Update trakt table
    task.state.trakt.table.movies = {
        ('tmdb', '158852'): ('imdb', 'tt1964418'),
        ('tmdb', '284674'): ('imdb', 'tt2091478')
    }
    task.state.trakt.table.shows = {}

    # Update map
    # - Movies
    task.map.add_one('1', '3',   ('imdb', 'tt1323594'))
    task.map.add_one('1', '5',   ('imdb', 'tt1375666'))
    task.map.add_one('1', '6',   ('imdb', 'tt0371746'))
    task.map.add_one('1', '7',   ('imdb', 'tt1228705'))
    task.map.add_one('1', '9',   ('imdb', 'tt0107290'))
    task.map.add_one('1', '12',  ('imdb', 'tt0993846'))
    task.map.add_one('1', '434', ('imdb', 'tt0080684'))
    task.map.add_one('1', '433', ('imdb', 'tt0076759'))
    task.map.add_one('1', '435', ('imdb', 'tt0086190'))
    task.map.add_one('1', '440', ('imdb', 'tt1392190'))

    task.map.add_one('4', '484', ('tmdb', '284674'))
    task.map.add_one('4', '485', ('tmdb', '251653'))
    task.map.add_one('4', '486', ('tmdb', '158852'))
    # - Shows
    task.map.add_one('2', '88',  ('tvdb', '84912'))
    task.map.add_one('2', '106', ('tvdb', '80348'))
    task.map.add_one('2', '101', ('tvdb', '79488'))

    # Build playlist mapper
    mapper = PlaylistMapper(task, {})

    # Load playlists
    mapper.plex.load(Plex['playlists'].get(1).first())
    mapper.trakt.load(Trakt['users/*/lists/*'].get('one', 'mixed'))

    # Match items between plex and trakt
    t_items, p_items = mapper.match()

    # Print items
    print_items(t_items)
    print_items(p_items)

    # Build dictionaries from items
    t_items = dict([
        (item[0], item[1:])
        for item in t_items
    ])

    p_items = dict([
        (item[0], item[1:])
        for item in p_items
    ])

    # Validate result
    assert t_items[(('imdb', 'tt0993846'),)][1] == (None, None)
    assert t_items[(('imdb', 'tt1375666'),)][1] == (None, None)
    assert t_items[(('tvdb', '79488'), 1, 2)][1] == (None, None)

    assert p_items[(('imdb', 'tt1228705'),)][2] == (None, None)


def print_items(items):
    for key, index, (p_index, p_item), (t_index, t_item) in items:
        # Build key
        key = list(key)
        key[0] = '/'.join(key[0])

        key = '/'.join([str(x) for x in key])

        # Build indices
        if p_index is None:
            p_index = '--'

        if t_index is None:
            t_index = '--'

        log.debug('[%-14s](%2s) - %50s <[%2s] - [%2s]> %r', key, index, p_item, p_index, t_index, t_item)
