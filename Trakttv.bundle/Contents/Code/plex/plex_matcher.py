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
    def match_episode_identifier(cls, p_season, p_episode, c_identifier, file_name=None):
        # Season number retrieval/validation (only except exact matches to p_season)
        if 'season' not in c_identifier:
            log.debug(IDENTIFIER_MISMATCH, file_name, 'identifier does not contain a season')
            return

        c_season = try_convert(c_identifier['season'], int)

        if c_season != p_season:
            log.debug(IDENTIFIER_MISMATCH, file_name, 'identifier with season %s does not match plex season %s' % (c_season, p_season))
            return

        # Episode number retrieval/validation
        c_episodes = None

        # Single or repeat-style episodes
        if 'episode' in c_identifier:
            episodes = c_identifier['episode']

            if not isinstance(episodes, (list, set)):
                episodes = [episodes]

            c_episodes = [try_convert(x, int) for x in episodes]

        # Extend-style episodes
        if 'episode_from' in c_identifier and 'episode_to' in c_identifier:
            c_from = try_convert(c_identifier['episode_from'], int)
            c_to = try_convert(c_identifier['episode_to'], int)

            if c_from is None or c_to is None:
                log.debug(IDENTIFIER_MISMATCH, file_name, 'identifier episode from or to value is not valid')
                return

            episodes = range(c_from, c_to + 1)

            # Ensure plex episode is inside extended episode range
            if p_episode in episodes:
                c_episodes = episodes
            else:
                log.debug(IDENTIFIER_MISMATCH, file_name, 'identifier with episodes %s does not contain plex episode %s' % (episodes, p_episode))
                return

        return c_episodes


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

        # Get plex identifier
        p_season = try_convert(video.get('parentIndex'), int)
        p_episode = try_convert(video.get('index'), int)

        # Ensure plex data is valid
        if p_season is None or p_episode is None:
            log.debug('Ignoring item with key "%s", invalid season or episode attribute', video.get('ratingKey'))
            return None, []

        # Find new episodes from identifiers
        c_episodes = [p_episode]

        for c_identifier in extended.chains[0].info['identifier']:
            if 'season' not in c_identifier:
                continue

            episodes = cls.match_episode_identifier(p_season, p_episode, c_identifier, file_name)
            if episodes is None:
                continue

            # Insert any new episodes found from identifier
            for episode in episodes:
                if episode in c_episodes:
                    continue

                c_episodes.append(episode)

        # Remove any episode identifiers that are more than 1 away
        c_episodes = cls.remove_distant(c_episodes, p_episode)

        return p_season, c_episodes
