from plex.plex_base import PlexBase


SHOW_SID_REGEX = Regex('com.plexapp.agents.(thetvdb|abstvdb|xbmcnfotv)://([-a-z0-9\.]+)')


class PlexMetadata(PlexBase):
    @classmethod
    def get(cls, rating_key):
        return cls.request('library/metadata/%s' % rating_key)

    @classmethod
    def get_guid(cls, rating_key):
        metadata = cls.get(rating_key)
        if metadata is None:
            return None

        return metadata.xpath('//Directory')[0].get('guid')

    @classmethod
    def get_show_sid(cls, rating_key):
        if not rating_key:
            Log.Warn("SID matching failed, ratingKey isn't valid")
            return None

        guid = PlexMetadata.get_guid(rating_key)

        match = SHOW_SID_REGEX.search(guid)
        if not match:
            Log.Warn('SID matching failed on guid: "%s"' % guid)
            return None

        return match.group(2)
