from plex import Plex
from plex_metadata.core.helpers import try_convert

import hashlib
import logging
import os

log = logging.getLogger(__name__)


class Matcher(object):
    def __init__(self):
        self.caper = self._construct_caper()

    def _construct_caper(self):
        # Caper (optional import)
        try:
            from caper import Caper
            return Caper()
        except ImportError, ex:
            log.info('Caper not available - "%s"', ex)
            return None

    @property
    def cache(self):
        return Plex.configuration.get('cache.matcher')

    def parse(self, file_name):
        identifier = None

        file_hash = self.md5(file_name)

        if self.cache is not None:
            # Try lookup identifier in cache
            identifier = self.cache.get(file_hash)

        # Parse new file_name
        if identifier is None and self.caper:
            # Parse file_name with Caper
            result = self.caper.parse(file_name)

            chain = result.chains[0] if result.chains else None

            # Get best identifier match from result
            identifier = chain.info.get('identifier', []) if chain else []

            if self.cache is not None:
                # Update cache
                self.cache[file_hash] = identifier

        return identifier

    def md5(self, value):
        m = hashlib.md5()
        m.update(value)

        return m.hexdigest()

    def process(self, metadata):
        if metadata.type == 'episode':
            return self.process_episode(metadata)

        raise ValueError('Unsupported metadata type "%s"' % metadata.type)

    def process_episode(self, episode):
        # Get plex identifier
        p_season = episode.season.index
        p_episode = episode.index

        # Ensure plex identifier is valid
        if p_season is None or p_episode is None:
            log.debug('Ignoring item with key "%s", invalid season or episode attribute', episode.rating_key)
            return None, []

        # Find new episodes from identifiers
        c_episodes = [p_episode]

        # Add extended episodes
        c_episodes.extend(self.extend_episode(episode.media.parts, (p_season, p_episode)))

        # Remove any episode identifiers that are more than 1 away
        c_episodes = self.remove_distant(c_episodes, p_episode)

        return p_season, c_episodes

    # TODO matcher preference
    def extend_episode(self, parts, p_identifier):
        if not parts:
            return []

        _, p_episode = p_identifier

        # Get just the name of the first part (without full path and extension)
        file_name = os.path.splitext(os.path.basename(parts[0].file))[0]

        # Parse file_name with caper (or get cached result)
        c_identifiers = self.parse(file_name)

        result = []
        for c_identifier in (c_identifiers or []):
            if 'season' not in c_identifier:
                continue

            episodes = self.match_episode(p_identifier, c_identifier)
            if episodes is None:
                continue

            # Insert any new episodes found from identifier
            for episode in episodes:
                if episode == p_episode:
                    continue

                result.append(episode)

        return result

    def match_episode(self, p_identifier, c_identifier):
        p_season, p_episode = p_identifier

        # Season number retrieval/validation (only except exact matches to p_season)
        if 'season' not in c_identifier:
            return

        c_season = try_convert(c_identifier['season'], int)
        if c_season != p_season:
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
                return

            episodes = range(c_from, c_to + 1)

            # Ensure plex episode is inside identifier episode range
            if p_episode in episodes:
                c_episodes = episodes
            else:
                return

        return c_episodes

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
            if abs(s[x] - s[x - step]) <= max_distance:
                result.append(s[x])
            else:
                break

        return result

# Global object
Default = Matcher()
