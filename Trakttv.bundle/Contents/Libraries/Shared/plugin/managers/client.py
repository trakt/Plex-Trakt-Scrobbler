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
            Client.machine_identifier == player['machine_identifier']
        )

    def or_create(self, player, fetch=False):
        player = self.manager.parse_player(player)

        try:
            # Create new client
            obj = self.manager.create(
                machine_identifier=player['machine_identifier']
            )

            # Update newly created object
            self.manager.update(obj, player, fetch)

            return obj
        except apsw.ConstraintError:
            # Return existing user
            return self(player)


class UpdateClient(Update):
    def __call__(self, obj, player, fetch=False):
        player = self.manager.parse_player(player)
        data = self.to_dict(obj, player, fetch)

        return super(UpdateClient, self).__call__(
            obj, data
        )

    def to_dict(self, obj, player, fetch=False):
        result = {
            'name': player['title']
        }

        # Fill `result` with available fields
        if player.get('platform'):
            result['platform'] = player['platform']

        if player.get('product'):
            result['product'] = player['product']

        if not fetch:
            # Return simple update
            return result

        # Fetch client details
        client = Plex.clients().get(player['machine_identifier'])

        if client:
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
        else:
            log.info('Unable to find client with machine_identifier %r', player['machine_identifier'])

        # Try match client against a rule
        return self.match(result, client, player)

    def match(self, result, client, player):
        # Apply global filters
        # TODO apply section filter
        if not Filters.is_valid_client(player) or\
           not Filters.is_valid_address(client):
            # Client didn't pass filters, update `account` attribute and return
            result['account'] = None

            return result

        # Find matching `ClientRule`
        address = client['address'] if client else None

        query = ClientRule.select().where((
            (ClientRule.machine_identifier == player['machine_identifier']) | (ClientRule.machine_identifier == None) &
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
            'machine_identifier': player.machine_identifier,
            'title': player.title,

            'platform': player.platform,
            'product': player.product
        }
