from plugin.core.filters import Filters
from plugin.core.helpers.variable import merge
from plugin.managers.core.base import Get, Manager, Update
from plugin.models import Client, ClientRule

from plex import Plex
import apsw
import logging

log = logging.getLogger(__name__)


class GetClient(Get):
    def __call__(self, player):
        player = self.manager.parse_player(player)

        return super(GetClient, self).__call__(
            Client.key == player['key']
        )

    def or_create(self, player, fetch=False, match=False):
        player = self.manager.parse_player(player)

        try:
            # Create new client
            obj = self.manager.create(
                key=player['key']
            )

            # Update newly created object
            self.manager.update(obj, player, fetch=fetch, match=match)

            return obj
        except apsw.ConstraintError:
            # Return existing user
            obj = self(player)

            if fetch or match:
                # Update existing `User`
                self.manager.update(obj, player, fetch=fetch, match=match)

            return obj


class UpdateClient(Update):
    def __call__(self, obj, player, fetch=False, match=False):
        player = self.manager.parse_player(player)
        data = self.to_dict(obj, player, fetch=fetch, match=match)

        return super(UpdateClient, self).__call__(
            obj, data
        )

    def to_dict(self, obj, player, fetch=False, match=False):
        result = {
            'name': player['title']
        }

        # Fill `result` with available fields
        if player.get('platform'):
            result['platform'] = player['platform']

        if player.get('product'):
            result['product'] = player['product']

        client = None

        if fetch or match:
            # Fetch client from plex server
            result, client = self.fetch(result, player)

        if match:
            # Try match client against a rule
            result = self.match(result, client, player)

        return result

    @staticmethod
    def fetch(result, player):
        # Fetch client details
        client = Plex.clients().get(player['key'])

        if not client:
            log.info('Unable to find client with key %r', player['key'])
            return result, None

        # Merge client details from plex API
        result = merge(result, dict([
            (key, getattr(client, key)) for key in [
                'device_class',
                'product',
                'version',

                'host',
                'address',
                'port',

                'protocol',
                'protocol_capabilities',
                'protocol_version'
            ] if getattr(client, key)
        ]))

        return result, client

    @staticmethod
    def match(result, client, player):
        # Apply global filters
        if not Filters.is_valid_client(player) or\
           not Filters.is_valid_address(client):
            # Client didn't pass filters, update `account` attribute and return
            result['account'] = None

            return result

        # Find matching `ClientRule`
        address = client['address'] if client else None

        query = ClientRule.select().where((
            (ClientRule.key == player['key']) | (ClientRule.key == None) &
            (ClientRule.name == player['title']) | (ClientRule.name == None) &
            (ClientRule.address == address) | (ClientRule.address == None)
        ))

        rules = list(query.execute())

        if len(rules) == 1:
            result['account'] = rules[0].account_id
        else:
            result['account'] = None

        return result


class ClientManager(Manager):
    get = GetClient
    update = UpdateClient

    model = Client

    @classmethod
    def parse_player(cls, player):
        if type(player) is dict:
            return player

        # Build user dict from object
        return {
            'key': player.machine_identifier,
            'title': player.title,

            'platform': player.platform,
            'product': player.product
        }
