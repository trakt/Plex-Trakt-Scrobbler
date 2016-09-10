from plex.objects.core.base import Descriptor, Property
from plex.objects.library.section import Section


class Metadata(Descriptor):
    section = Property(resolver=lambda: Metadata.construct_section)

    key = Property
    guid = Property
    rating_key = Property('ratingKey')
    extra_key = Property('primaryExtraKey')

    title = Property
    title_sort = Property('titleSort')
    title_sort_saved = Property('titleSortSaved')
    title_original = Property('originalTitle')

    audience_rating = Property('audienceRating', float)
    audience_rating_image = Property('audienceRatingImage')

    content_rating = Property('contentRating')
    content_rating_age = Property('contentRatingAge', int)

    rating = Property(type=float)
    rating_count = Property('ratingCount')
    rating_image = Property('ratingImage')

    studio = Property
    summary = Property
    tagline = Property
    year = Property(type=int)

    thumb = Property

    source_icon = Property('sourceIcon')
    source_title = Property('sourceTitle')
    url = Property('url')

    deferred = Property(type=(int, bool))

    added_at = Property('addedAt', int)
    created_at_accuracy = Property('createdAtAccuracy')
    created_at_tzoffset = Property('createdAtTZOffset', int)
    deleted_at = Property('deletedAt', int)
    first_scan_added_at = Property('firstScanAddedAt', int)
    last_viewed_at = Property('lastViewedAt', int)
    originally_available_at = Property('originallyAvailableAt')

    @staticmethod
    def construct_section(client, node):
        attribute_map = {
            'key': 'librarySectionID',
            'id': 'librarySectionID',
            'uuid': 'librarySectionUUID',
            'path': 'librarySectionKey',

            'title': 'librarySectionTitle'
        }

        return Section.construct(client, node, attribute_map, child=True)
