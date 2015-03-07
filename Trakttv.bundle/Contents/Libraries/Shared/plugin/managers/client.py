from plugin.core.helpers.variable import merge
from plugin.managers.core.base import Get, Manager, Update
from plugin.models import Client, ClientRule

from plex import Plex
import apsw
import logging

log = logging.getLogger(__name__)


class GetClient(Get):
    def __call__(self, player):
        return super(GetClient, self).__call__(
            Client.machine_identifier == player.machine_identifier
        )

    def or_create(self, player, fetch=False):
        try:
            # Create new client
            obj = self.manager.create(
                machine_identifier=player.machine_identifier
            )

            # Update newly created object
            self.manager.update(obj, player, fetch)

            return obj
        except apsw.ConstraintError:
            # Return existing user
            return self(player)


class UpdateClient(Update):
    def __call__(self, obj, player, fetch=False):
        data = self.to_dict(obj, player, fetch)

        return super(UpdateClient, self).__call__(
            obj, data
        )

    def to_dict(self, obj, player, fetch=False):
        result = {
            'name': player.title,

            'platform': player.platform,
            'product': player.product
        }

        if not fetch:
            # Return simple update
            return result

        # Fetch client details
        client = Plex.clients().get(player.machine_identifier)

        if not client:
            log.warn('Unable to find client with machine_identifier %r', player.machine_identifier)
            return result

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

        # Find matching `ClientRule`
        query = ClientRule.select().where((
            (ClientRule.machine_identifier == player.machine_identifier) | (ClientRule.machine_identifier == None) &
            (ClientRule.name == player.title) | (ClientRule.name == None) &
            (ClientRule.address == client.address) | (ClientRule.address == None)
        ))

        rules = list(query.execute())

        if len(rules) != 1:
            return result

        result['account'] = rules[0].account_id

        return result


class ClientManager(Manager):
    get = GetClient
    update = UpdateClient

    model = Client
