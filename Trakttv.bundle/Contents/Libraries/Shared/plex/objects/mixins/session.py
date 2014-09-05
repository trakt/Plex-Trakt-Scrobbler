from plex.objects.core.base import Descriptor, Property, DescriptorMixin


class SessionMixin(DescriptorMixin):
    session = Property(resolver=lambda: SessionMixin.construct_session)

    @staticmethod
    def construct_session(client, node):
        return Session.construct(client, node, child=True)


class Session(Descriptor):
    key = Property('sessionKey')
