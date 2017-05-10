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

    country_code = Property('countryCode')
    streaming_brain_version = Property('streamingBrainVersion', int)

    allow_camera_upload = Property('allowCameraUpload', (int, bool))
    allow_channel_access = Property('allowChannelAccess', (int, bool))
    allow_media_deletion = Property('allowMediaDeletion', (int, bool))
    allow_sharing = Property('allowSharing', (int, bool))
    allow_sync = Property('allowSync', (int, bool))

    background_processing = Property('backgroundProcessing', (int, bool))
    companion_proxy = Property('companionProxy', (int, bool))
    diagnostics = Property(resolver=lambda: Detail.parse_diagnostics)
    event_stream = Property('eventStream', (int, bool))
    hub_search = Property('hubSearch', (int, bool))
    item_clusters = Property('itemClusters', (int, bool))
    media_providers = Property('mediaProviders', (int, bool))
    photo_auto_tag = Property('photoAutoTag', (int, bool))
    plugin_host = Property('pluginHost', (int, bool))
    read_only_libraries = Property('readOnlyLibraries', (int, bool))
    updater = Property('updater', (int, bool))
    voice_search = Property('voiceSearch', (int, bool))

    certificate = Property(type=(int, bool))
    multiuser = Property(type=(int, bool))
    owner_features = Property('ownerFeatures')
    sync = Property(type=(int, bool))

    start_state = Property('startState')

    silverlight = Property('silverlightInstalled', (int, bool))
    soundflower = Property('soundflowerInstalled', (int, bool))
    flash = Property('flashInstalled', (int, bool))
    webkit = Property(type=(int, bool))

    cookie_parameters = Property('requestParametersInCookie', (int, bool))

    @staticmethod
    def construct_myplex(client, node):
        return MyPlexDetail.construct(client, node, child=True)

    @staticmethod
    def construct_transcoder(client, node):
        return TranscoderDetail.construct(client, node, child=True)

    @classmethod
    def parse_diagnostics(cls, client, node):
        diagnostics = cls.helpers.get(node, 'diagnostics')

        if not diagnostics:
            return ['diagnostics'], []

        return ['diagnostics'], diagnostics.split(',')


class MyPlexDetail(Descriptor):
    enabled = Property('myPlex', bool)

    username = Property('myPlexUsername')

    mapping_state = Property('myPlexMappingState')
    signin_state = Property('myPlexSigninState')

    subscription = Property('myPlexSubscription', (int, bool))


class TranscoderDetail(Descriptor):
    audio = Property('transcoderAudio', (int, bool))
    lyrics = Property('transcoderLyrics', (int, bool))
    photo = Property('transcoderPhoto', (int, bool))
    subtitles = Property('transcoderSubtitles', (int, bool))
    video = Property('transcoderVideo', (int, bool))

    video_bitrates = Property('transcoderVideoBitrates')
    video_qualities = Property('transcoderVideoQualities')
    video_remux_only = Property('transcoderVideoRemuxOnly', (int, bool))
    video_resolutions = Property('transcoderVideoResolutions')

    active_video_sessions = Property('transcoderActiveVideoSessions', int)
