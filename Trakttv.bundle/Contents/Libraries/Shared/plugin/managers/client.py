from plugin.core.helpers.variable import merge
from plugin.managers.core.base import Manager
from plugin.models import Client

from plex import Plex
import logging

log = logging.getLogger(__name__)


class ClientManager(Manager):
    model = Client

    @classmethod
    def from_session(cls, session, fetch=False):
        machine_identifier = session.player.machine_identifier

        return cls.get_or_create(
            session.player,

            Client.machine_identifier == machine_identifier,

            fetch=fetch,
            on_create={
                'machine_identifier': machine_identifier
            }
        )

    @classmethod
    def to_dict(cls, obj, player, fetch=False):
        result = {
            'name': player.title,

            'platform': player.platform,
            'product': player.product
        }

        if not fetch:
            # Return simple update
            return result

        client = Plex.clients().get(player.machine_identifier)

        if not client:
            log.warn('Unable to find client with machine_identifier %r', player.machine_identifier)
            return result

        return merge(result, dict([
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
