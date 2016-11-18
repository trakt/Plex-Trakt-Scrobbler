from plugin.core.filters import Filters
from plugin.core.helpers.variable import merge
from plugin.managers.core.base import Get, Manager, Update
from plugin.managers.core.exceptions import ClientFilteredException
from plugin.models import Client, ClientRule

from exception_wrappers.libraries import apsw
from plex import Plex
import logging
import peewee

log = logging.getLogger(__name__)


class GetClient(Get):
    def __call__(self, player):
        player = self.manager.parse_player(player)

        return super(GetClient, self).__call__(
            Client.key == player['key']
        )

    def or_create(self, player, fetch=False, match=False, filtered_exception=False):
        player = self.manager.parse_player(player)

        try:
            # Create new client
            obj = self.manager.create(
                key=player['key']
            )

            # Update newly created object
            self.manager.update(
                obj, player,

                fetch=fetch,
                match=match,
                filtered_exception=filtered_exception
            )

            return obj
        except (apsw.ConstraintError, peewee.IntegrityError):
            # Return existing user
            obj = self(player)

            if fetch or match:
                # Update existing `User`
                self.manager.update(
                    obj, player,

                    fetch=fetch,
                    match=match,
                    filtered_exception=filtered_exception
                )

            return obj


class UpdateClient(Update):
    def __call__(self, obj, player, fetch=False, match=False, filtered_exception=False):
        player = self.manager.parse_player(player)

        filtered, data = self.to_dict(
            obj, player,

            fetch=fetch,
            match=match
        )

        updated = super(UpdateClient, self).__call__(
            obj, data
        )

        if filtered and filtered_exception:
            raise ClientFilteredException

        return updated

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
        filtered = False

        if fetch or match:
            # Fetch client from plex server
            result, client = self.fetch(result, player)

        if match:
            # Try match client against a rule
            filtered, result = self.match(
                result, client, player
            )

        return filtered, result

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

            return True, result

        # Find matching `ClientRule`
        address = client['address'] if client else None

        rule = (ClientRule
            .select()
            .where(
                (ClientRule.key == player['key']) |
                (ClientRule.key == '*') |
                (ClientRule.key == None),

                (ClientRule.name == player['title']) |
                (ClientRule.name == '*') |
                (ClientRule.name == None),

                (ClientRule.address == address) |
                (ClientRule.address == '*') |
                (ClientRule.address == None)
            )
            .order_by(
                ClientRule.priority.asc()
            )
            .first()
        )

        log.debug('Activity matched against rule: %r', rule)

        if rule:
            # Process rule
            if rule.account_id is not None:
                result['account'] = rule.account_id
            else:
                return True, result
        else:
            result['account'] = None

        return False, result


class ClientManager(Manager):
    get = GetClient
    update = UpdateClient

    model = Client

    @classmethod
    def parse_player(cls, player):
        if type(player) is not dict:
            # Build user dict from object
            player = {
                'key': player.machine_identifier,
                'title': player.title,

                'platform': player.platform,
                'product': player.product
            }

        # Strip "_Video" suffix from the `key`
        if player.get('key') and player['key'].endswith('_Video'):
            # Update player key
            player['key'] = player['key'].rstrip('_Video')

        return player
