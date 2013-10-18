PMS_URL = 'http://localhost:32400%s'


class PMS:
    def __init__(self):
        pass

    @classmethod
    def get_server_info(cls):
        return XML.ElementFromURL(PMS_URL % '', errors='ignore')

    @classmethod
    def get_server_version(cls, default=None):
        server_info = cls.get_server_info()
        if not server_info:
            return default

        return server_info.attrib.get('version') or default

    @classmethod
    def get_status(cls):
        return XML.ElementFromURL(PMS_URL % '/status/sessions', errors='ignore')

    @classmethod
    def get_video_session(cls, session_key):
        try:
            xml_content = cls.get_status().xpath('//MediaContainer/Video')

            for section in xml_content:
                if section.get('sessionKey') == session_key and '/library/metadata' in section.get('key'):
                    return section

        except Ex.HTTPError:
            Log.Error('Failed to connect to PMS.')
        except Ex.URLError:
            Log.Error('Failed to connect to PMS.')

        Log.Warn('Session not found')
        return None

    @classmethod
    def get_metadata(cls, key):
        return XML.ElementFromURL(PMS_URL % ('/library/metadata/%s' % key), errors='ignore')

    @classmethod
    def get_metadata_guid(cls, key):
        return cls.get_metadata(key).xpath('//Directory')[0].get('guid')

    @classmethod
    def get_metadata_leaves(cls, key):
        return XML.ElementFromURL(PMS_URL % ('/library/metadata/%s/allLeaves' % key), errors='ignore')

    @classmethod
    def get_sections(cls):
        return XML.ElementFromURL(PMS_URL % '/library/sections', errors='ignore').xpath('//Directory')

    @classmethod
    def get_section(cls, name):
        return XML.ElementFromURL(PMS_URL % ('/library/sections/%s/all' % name), errors='ignore')

    @classmethod
    def get_section_directories(cls, section):
        return cls.get_section(section).xpath('//Directory')

    @classmethod
    def get_section_videos(cls, section):
        return cls.get_section(section).xpath('//Video')

    @classmethod
    def scrobble(cls, video):
        if video.get('viewCount') > 0:
            Log('video has already been marked as seen')
            return False

        HTTP.Request('http://localhost:32400/:/scrobble?identifier=com.plexapp.plugins.library&key=%s' % (
            video.get('ratingKey')
        ), immediate=True)

        return True

    @classmethod
    def rate(cls, video, rating):
        HTTP.Request('http://localhost:32400/:/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (
            video.get('ratingKey'), rating
        ), immediate=True)

        return True
