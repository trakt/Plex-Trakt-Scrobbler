from plex_database.core import db
from plex_database.models.library_section import LibrarySection
from plex_database.models.metadata_item import MetadataItem
from plex_database.models.section_location import SectionLocation

from peewee import *


class MediaItem(Model):
    class Meta:
        database = db
        db_table = 'media_items'

    library_section = ForeignKeyField(LibrarySection, null=True, related_name='media_items')
    section_location = ForeignKeyField(SectionLocation, null=True, related_name='media_items')
    metadata_item = ForeignKeyField(MetadataItem, null=True, related_name='media_items')

    type_id = IntegerField(null=True)

    width = IntegerField(null=True)
    height = IntegerField(null=True)

    size = BigIntegerField(null=True)
    duration = IntegerField(null=True)
    bitrate = IntegerField(null=True)

    container = CharField(null=True)
    audio_codec = CharField(null=True)
    video_codec = CharField(null=True)

    # Audio
    audio_channels = IntegerField(null=True)

    # Video
    display_aspect_ratio = FloatField(null=True)
    display_offset = IntegerField(null=True)
    frames_per_second = FloatField(null=True)
    interlaced = BooleanField(null=True)
    sample_aspect_ratio = FloatField(null=True)

    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)
    deleted_at = DateTimeField(null=True)

    hints  = CharField(null=True)
    media_analysis_version = IntegerField(default=0)
    optimized_for_streaming = BooleanField(null=True)
    settings  = CharField(null=True)
    source  = CharField(null=True)

    extra_data = CharField(null=True)
