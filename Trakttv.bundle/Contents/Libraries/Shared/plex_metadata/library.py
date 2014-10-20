from plex import Plex
from plex.core.helpers import to_iterable
from plex_metadata.guid import Guid
from plex_metadata.matcher import Default as Matcher
from plex_metadata.metadata import Default as Metadata


class Library(object):
    @classmethod
    def all(cls, types=None, keys=None, titles=None):
        types = to_iterable(types)

        sections = Plex['library'].sections().filter(types, keys, titles)
        result = {}

        for section in sections:
            if section.type not in result:
                result[section.type] = {}

            for item in section.all():
                cls.item_map(result[section.type], item)

        if types and len(types) == 1:
            # Return single type-map if only one was requested
            return result.get(types[0], {})

        return result

    @classmethod
    def episodes(cls, key, show=None, flat=True):
        result = {}

        container = Plex['library/metadata'].all_leaves(key)

        if not container:
            return None

        for item in container:
            if show is not None:
                item.show = show

            season, episodes = Matcher.process(item)

            if season is None or not episodes:
                continue

            if not flat and season not in result:
                result[season] = {}

            for episode in episodes:
                if flat:
                    result[season, episode] = item
                else:
                    result[season][episode] = item

        return result

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
