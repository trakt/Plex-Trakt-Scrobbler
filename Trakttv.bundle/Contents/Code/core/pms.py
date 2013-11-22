from core.network import request

PMS_URL = 'http://localhost:32400%s'


class PMS:
    def __init__(self):
        pass

    @classmethod
    def get_server_info(cls):
        response = request(PMS_URL % '', 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_server_version(cls, default=None):
        server_info = cls.get_server_info()
        if not server_info:
            return default

        return server_info.attrib.get('version') or default

    @classmethod
    def get_status(cls):
        response = request(PMS_URL % '/status/sessions', 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_video_session(cls, session_key):
        status = cls.get_status()
        if not status:
            Log.Warn('Status request failed, unable to connect to server')
            return None

        for section in status.xpath('//MediaContainer/Video'):
            if section.get('sessionKey') == session_key and '/library/metadata' in section.get('key'):
                return section

        Log.Warn('Session not found')
        return None

    @classmethod
    def get_metadata(cls, key):
        response = request(PMS_URL % ('/library/metadata/%s' % key), 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_metadata_guid(cls, key):
        metadata = cls.get_metadata(key)
        if not metadata:
            return None

        return metadata.xpath('//Directory')[0].get('guid')

    @classmethod
    def get_metadata_leaves(cls, key):
        response = request(PMS_URL % ('/library/metadata/%s/allLeaves' % key), 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_sections(cls):
        response = request(PMS_URL % '/library/sections', 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_section(cls, name):
        response = request(PMS_URL % ('/library/sections/%s/all' % name), 'xml')
        if not response:
            return None

        return response.data

    @classmethod
    def get_section_directories(cls, section_name):
        section = cls.get_section(section_name)
        if not section:
            return None

        return section.xpath('//Directory')

    @classmethod
    def get_section_videos(cls, section_name):
        section = cls.get_metadata(section_name)
        if not section:
            return None

        return section.xpath('//Video')

    @classmethod
    def scrobble(cls, video):
        if video.get('viewCount') > 0:
            Log('video has already been marked as seen')
            return False

        response = request(PMS_URL % '/:/scrobble?identifier=com.plexapp.plugins.library&key=%s' % (
            video.get('ratingKey')
        ))

        return response is not None

    @classmethod
    def rate(cls, video, rating):
        response = request(PMS_URL % '/:/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (
            video.get('ratingKey'), rating
        ))

        return response is not None
