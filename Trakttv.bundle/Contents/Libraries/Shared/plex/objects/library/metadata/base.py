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
    title_original = Property('originalTitle')

    audience_rating = Property('audienceRating', float)
    audience_rating_image = Property('audienceRatingImage')

    rating_count = Property('ratingCount')
    rating_image = Property('ratingImage')

    summary = Property

    thumb = Property

    source_title = Property('sourceTitle')

    added_at = Property('addedAt', int)
    last_viewed_at = Property('lastViewedAt', int)

    @staticmethod
    def construct_section(client, node):
        attribute_map = {
            'key': 'librarySectionID',
            'uuid': 'librarySectionUUID',
            'title': 'librarySectionTitle'
        }

        return Section.construct(client, node, attribute_map, child=True)
