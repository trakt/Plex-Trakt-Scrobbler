from plex.objects.core.base import Property
from plex.objects.server import Server


class Client(Server):
    product = Property
    device_class = Property('deviceClass')

    protocol = Property
    protocol_version = Property('protocolVersion', type=int)
    protocol_capabilities = Property('protocolCapabilities')
