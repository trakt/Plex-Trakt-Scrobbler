from plex.objects.core.base import Descriptor, Property, DescriptorMixin
from plex.objects.player import Player
from plex.objects.transcode_session import TranscodeSession
from plex.objects.user import User


class SessionMixin(DescriptorMixin):
    session = Property(resolver=lambda: SessionMixin.construct_session)

    @staticmethod
    def construct_session(client, node):
        return Session.construct(client, node, child=True)


class Session(Descriptor):
    key = Property('sessionKey', int)

    user = Property(resolver=lambda: Session.construct_user)
    player = Property(resolver=lambda: Session.construct_player)
    transcode_session = Property(resolver=lambda: Session.construct_transcode_session)

    @staticmethod
    def construct_user(client, node):
        return User.construct(client, node.find('User'), child=True)

    @staticmethod
    def construct_player(client, node):
        return Player.construct(client, node.find('Player'), child=True)

    @staticmethod
    def construct_transcode_session(client, node):
        return TranscodeSession.construct(client, node.find('TranscodeSession'), child=True)
