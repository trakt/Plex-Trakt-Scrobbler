from plex.objects.core.base import Descriptor, Property
from plex.objects.container import Container


class Detail(Container):
    myplex = Property(resolver=lambda: Detail.construct_myplex)
    transcoder = Property(resolver=lambda: Detail.construct_transcoder)

    friendly_name = Property('friendlyName')

    machine_identifier = Property('machineIdentifier')
    version = Property

    platform = Property
    platform_version = Property('platformVersion')

    multiuser = Property(type=bool)
    start_state = Property('startState')
    sync = Property(type=bool)

    silverlight = Property('silverlightInstalled', bool)
    soundflower = Property('soundflowerInstalled', bool)
    flash = Property('flashInstalled', bool)
    webkit = Property(type=bool)

    cookie_parameters = Property('requestParametersInCookie', bool)

    @staticmethod
    def construct_myplex(client, node):
        return MyPlexDetail.construct(client, node, child=True)

    @staticmethod
    def construct_transcoder(client, node):
        return TranscoderDetail.construct(client, node, child=True)


class MyPlexDetail(Descriptor):
    enabled = Property('myPlex', type=bool)

    username = Property('myPlexUsername')

    mapping_state = Property('myPlexMappingState')
    signin_state = Property('myPlexSigninState')

    subscription = Property('myPlexSubscription', bool)


class TranscoderDetail(Descriptor):
    audio = Property('transcoderAudio', bool)
    video = Property('transcoderVideo', bool)

    video_bitrates = Property('transcoderVideoBitrates')
    video_qualities = Property('transcoderVideoQualities')
    video_resolutions = Property('transcoderVideoResolutions')

    active_video_sessions = Property('transcoderActiveVideoSessions', int)
