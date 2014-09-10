from plex import Plex
from plex_metadata.guid import Guid
from plex_metadata.metadata import Default as Metadata


class Library(object):
    @classmethod
    def all(cls, titles=None, keys=None, types=None):
        result = {}

        sections = Plex['library'].sections().filter(titles, keys, types)

        for section in sections:
            if section.type not in result:
                result[section.type] = {}

            for item in section.all():
                print '[%s] %s' % (section.title, item.title)

                cls.item_map(result[section.type], item)

        return result

    @classmethod
    def episodes(cls, key, parent=None):
        pass

    @classmethod
    def item_map(cls, table, item):
        metadata = Metadata.get(item.rating_key)

        # Update with extended information
        item.guid = metadata.guid

        # Parse guid
        guid = Guid.parse(item.guid)
        key = (guid.agent, guid.sid)

        # Map item into table
        if key not in table:
            table[key] = []

        table[key].append(item)
        return True
