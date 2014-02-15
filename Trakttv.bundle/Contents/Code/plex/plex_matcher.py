from core.helpers import try_convert
from core.logger import Logger
from plex.plex_base import PlexBase
from caper import Caper
import types
import os

log = Logger('plex.plex_matcher')


IDENTIFIER_MISMATCH = 'Identifier parsing mismatch on "%s" (%s), using plex identifier'


class PlexMatcher(PlexBase):
    current = None

    @classmethod
    def get_parser(cls):
        """
        :rtype: Caper
        """
        if cls.current is None:
            log.info('Initializing caper parsing library')
            cls.current = Caper()

        return cls.current

    @staticmethod
    def merge_dicts(dicts):
        result = {}

        for d in dicts:
            for key, value in d.items():
                if key in result:
                    # Multiple items, append or switch to list
                    if isinstance(result[key], list):
                        result[key].append(value)
                    else:
                        result[key] = [result[key], value]
                else:
                    result[key] = value

        return result

    @classmethod
    def merge_info(cls, info):
        result = {}

        for key, value in info.items():
            if not isinstance(value, list):
                continue

            if isinstance(value[0], dict):
                result[key] = cls.merge_dicts(value)
            else:
                result[key] = value

        return result

    @classmethod
    def get_chain_identifier(cls, info):
        info = cls.merge_info(info)
        identifier = info.get('identifier')

        for key, value in identifier.items():
            if key not in ['season', 'episode', 'episode_from', 'episode_to']:
                continue

            if isinstance(value, types.StringTypes):
                identifier[key] = try_convert(value, int)
            elif isinstance(value, list):
                # For repeat style identifiers (S01E10E11, etc..)
                identifier[key] = set([try_convert(x, int) for x in value])

        return identifier

    @classmethod
    def remove_distant(cls, l, base=None, start=0, stop=None, step=1, max_distance=1):
        s = sorted(l)
        result = []

        if base is not None:
            bx = s.index(base)

            left = s[:bx + 1]
            result.extend(cls.remove_distant(left, start=len(left) - 2, stop=-1, step=-1, max_distance=max_distance))

            result.append(base)

            right = s[bx:]
            result.extend(cls.remove_distant(right, start=1, step=1, max_distance=max_distance))

            return result

        if stop is None:
            stop = len(s)

        for x in xrange(start, stop, step):
            if abs(s[x] -  s[x - step]) <= max_distance:
                result.append(s[x])
            else:
                break

        return result

    @classmethod
    def get_episode_identifier(cls, video):
        # Parse filename for extra info
        parts = video.find('Media').findall('Part')
        if not parts:
            log.warn('Item "%s" has no parts', video.get('ratingKey'))
            return None, []

        # Get just the name of the first part (without full path and extension)
        file_name = os.path.splitext(os.path.basename(parts[0].get('file')))[0]

        # TODO what is the performance of this like?
        # TODO maybe add the ability to disable this in settings ("Identification" option, "Basic" or "Accurate")
        extended = cls.get_parser().parse(file_name)

        identifier = cls.get_chain_identifier(extended.chains[0].info) if extended.chains else None

        # Get plex identifier
        season = try_convert(video.get('parentIndex'), int)
        episode = try_convert(video.get('index'), int)

        # Ensure season and episode numbers are valid
        if season is None or episode is None:
            log.debug('Ignoring item with key "%s", invalid season or episode attribute', video.get('ratingKey'))
            return None, []

        if identifier:
            # Ensure extended season matches plex
            if 'season' in identifier:
                seasons = identifier['season']

                if not isinstance(seasons, (list, set)):
                    seasons = [seasons]

                # Reject anything that doesn't match the plex season
                seasons = cls.remove_distant(seasons, season, max_distance=0)

                if season not in seasons or len(seasons) > 1:
                    log.debug(IDENTIFIER_MISMATCH, file_name, 'season: extended %s does not match plex %s' % (seasons, season))
            else:
                log.debug(IDENTIFIER_MISMATCH, file_name, 'season: extended does not exist')
                return season, [episode]

            # Ensure extended single episode matches plex
            if 'episode' in identifier:
                episodes = identifier['episode']

                if not isinstance(episodes, (list, set)):
                    episodes = [episodes]

                # Remove any episode identifiers that are more than 1 away
                episodes = cls.remove_distant(episodes, episode)

                if episode not in episodes:
                    log.debug(IDENTIFIER_MISMATCH, file_name, 'episode: extended %s does not contain plex %s' % (episodes, episode))

                return season, episodes

            if 'episode_from' in identifier and 'episode_to' in identifier:
                episodes = range(identifier.get('episode_from'), identifier.get('episode_to') + 1)

                # Ensure plex episode is inside extended episode range
                if episode not in episodes:
                    log.debug(IDENTIFIER_MISMATCH, file_name, 'episode: extended %s does not contain plex %s' %(episodes, episode))
                    return season, [episode]

                return season, episodes

        return season, [episode]
