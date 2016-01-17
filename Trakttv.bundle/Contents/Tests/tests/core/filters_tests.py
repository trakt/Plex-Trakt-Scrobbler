from plex_mock.models import LibraryMetadata, LibrarySection
from plugin.core.environment import Environment
from plugin.core.filters import Filters

import pytest

#
# match
#

def test_missing_preference():
    Environment.prefs['scrobble_names'] = None

    assert Filters.is_valid_user({'title': 'one'}) is True

#
# is_valid_user
#

def test_user_basic():
    Environment.prefs['scrobble_names'] = 'one'

    assert Filters.is_valid_user({'title': 'one'}) is True


def test_user_inverted():
    Environment.prefs['scrobble_names'] = 'one, -two'

    assert Filters.is_valid_user({'title': 'one'}) is True
    assert Filters.is_valid_user({'title': 'two'}) is False


def test_user_wildcard():
    Environment.prefs['scrobble_names'] = '*'

    assert Filters.is_valid_user({'title': 'one'}) is True


def test_user_empty():
    Environment.prefs['scrobble_names'] = ''

    assert Filters.is_valid_user({'title': 'one'}) is True

#
# is_valid_client
#

def test_client_basic_positive():
    Environment.prefs['scrobble_clients'] = 'pcone'

    assert Filters.is_valid_client({'title': 'PC-One'}) is True
    assert Filters.is_valid_client({'title': 'PC-Two', 'product': 'DLNA'}) is False


def test_client_basic_inverted():
    Environment.prefs['scrobble_clients'] = 'pcone, -pctwo'

    assert Filters.is_valid_client({'title': 'PC-One'}) is True
    assert Filters.is_valid_client({'title': 'PC-Two'}) is False
    assert Filters.is_valid_client({'title': 'PC-Three', 'product': 'DLNA'}) is False


def test_client_dlna_positive():
    Environment.prefs['scrobble_clients'] = '#dlna'

    assert Filters.is_valid_client({'title': 'PC-One'}) is False
    assert Filters.is_valid_client({'title': 'PC-Two', 'product': 'DLNA'}) is True


def test_client_dlna_inverted():
    Environment.prefs['scrobble_clients'] = '-#dlna'

    assert Filters.is_valid_client({'title': 'PC-One'}) is True
    assert Filters.is_valid_client({'title': 'PC-Two', 'product': 'DLNA'}) is False


def test_client_dlna_invalid():
    Environment.prefs['scrobble_clients'] = '#, pcone'

    assert Filters.is_valid_client({'title': 'PC-One'}) is True


def test_client_wildcard():
    Environment.prefs['scrobble_clients'] = '*'

    assert Filters.is_valid_client({'title': 'PC-One'}) is True
    assert Filters.is_valid_client({'title': 'PC-Two', 'product': 'DLNA'}) is True


def test_client_empty():
    Environment.prefs['scrobble_clients'] = ''

    assert Filters.is_valid_client({'title': 'PC-One'}) is True
    assert Filters.is_valid_client({'title': 'PC-Two', 'product': 'DLNA'}) is True


def test_client_invalid():
    Environment.prefs['scrobble_clients'] = 'pcone'

    assert Filters.is_valid_client({}) is False

#
# is_valid_metadata_section
#

def test_metadata_section_basic():
    # Basic
    Environment.prefs['filter_sections'] = 'one (movies)'

    assert Filters.is_valid_metadata_section(
        LibraryMetadata(section=LibrarySection(title='One (Movies)'))
    ) is True

#
# is_valid_section_name
#

def test_section_name_basic():
    # Basic
    Environment.prefs['filter_sections'] = 'one (movies)'

    assert Filters.is_valid_section_name('One (Movies)') is True


def test_section_name_invalid_name():
    # Basic
    Environment.prefs['filter_sections'] = 'one (movies)'

    assert Filters.is_valid_section_name('') is True

#
# is_valid_address
#

def test_address_basic():
    # Filter Address
    Environment.prefs['filter_networks'] = '10.20.30.40'

    assert Filters.is_valid_address({
        'address': '10.20.30.40'
    }) is True

    # Filter Subnet
    Environment.prefs['filter_networks'] = '10.20.30.0/24'

    assert Filters.is_valid_address({
        'address': '10.20.30.40'
    }) is True


def test_address_invalid_client():
    # Empty Address
    Environment.prefs['filter_networks'] = '10.20.30.40'

    assert Filters.is_valid_address({
        'address': None
    }) is False

    # Malformed Address
    Environment.prefs['filter_networks'] = '10.20.30.40'

    assert Filters.is_valid_address({
        'address': '10.20.30'
    }) is False


def test_address_invalid_filter():
    # Empty Filter
    Environment.prefs['filter_networks'] = ','

    assert Filters.is_valid_address({
        'address': '10.20.30.40'
    }) is False

    # Malformed Filter
    Environment.prefs['filter_networks'] = '10.20.30/24'

    assert Filters.is_valid_address({
        'address': '10.20.30.40'
    }) is False
