from plex import Plex
from plex.lib import six
from plex_metadata.core.helpers import try_convert

import hashlib
import logging

log = logging.getLogger(__name__)


class Matcher(object):
    def __init__(self, cache=None, client=None):
        self._cache = cache
        self._client = client

        # Construct `Caper` parser
        self._caper = self._construct_caper()
        self._caper_enabled = True

        self._extend_enabled = True

    def configure(self, cache=None, client=None, caper_enabled=True, extend_enabled=True):
        self.cache = cache
        self.client = client

        self.caper_enabled = caper_enabled
        self.extend_enabled = extend_enabled

    #
    # Properties
    #

    @property
    def cache(self):
        if self._cache is not None:
            return self._cache

        if self._client:
            return self._client.configuration.get('cache.matcher')

        return Plex.configuration.get('cache.matcher')

    @cache.setter
    def cache(self, value):
        self._cache = value

    @property
    def client(self):
        if self._client:
            return self._client

        return Plex.client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def caper_enabled(self):
        return self._caper_enabled

    @caper_enabled.setter
    def caper_enabled(self, enabled):
        if self._caper_enabled == enabled:
            # state hasn't changed
            return

        # state changed
        if enabled:
            self._caper = self._construct_caper()
        else:
            self._caper = None

        self._caper_enabled = enabled

        log.info('"caper" feature has been %s', 'enabled' if enabled else 'disabled')

    @property
    def extend_enabled(self):
        return self._extend_enabled

    @extend_enabled.setter
    def extend_enabled(self, enabled):
        if self._extend_enabled == enabled:
            # state hasn't changed
            return

        self._extend_enabled = enabled

        log.info('"extend" feature has been %s', 'enabled' if enabled else 'disabled')

    @staticmethod
    def _construct_caper():
        # Caper (optional import)
        try:
            from caper import Caper
            return Caper()
        except ImportError as ex:
            log.info('Caper not available - "%s"', ex)
            return None

    def parse(self, file_name):
        cache = self.cache
        identifier = None

        file_hash = self.md5(file_name)

        if cache is not None:
            # Try lookup identifier in cache
            identifier = cache.get(file_hash)

        # Parse new file_name
        if identifier is None and self._caper:
            # Parse file_name with Caper
            result = self._caper.parse(file_name)

            if not result:
                return None

            chain = result.chains[0] if result.chains else None

            # Get best identifier match from result
            identifier = chain.info.get('identifier', []) if chain else []

            if cache is not None:
                # Update cache
                cache[file_hash] = identifier

        return identifier

    @staticmethod
    def md5(value):
        if isinstance(value, six.text_type):
            value = value.encode('utf-8')

        m = hashlib.md5()
        m.update(value)

        return m.hexdigest()

    @staticmethod
    def name(path):
        left = path.rfind('\\')

        if left < 0:
            left = path.rfind('/')

        if left < 0:
            return None

        right = path.rfind('.', left)

        if right < 0:
            return None

        return path[left + 1:right]

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

        if episode.media and episode.media.parts and self._extend_enabled:
            # Add extended episodes
            c_episodes.extend(self.extend_episode(episode.media.parts[0].file, (p_season, p_episode)))

            # Remove any episode identifiers that are more than 1 away
            c_episodes = self.remove_distant(c_episodes, p_episode)
        elif self._extend_enabled:
            log.warn('Item with key "%s" has no media parts, unable to use the extended matcher', episode.rating_key)

        return p_season, c_episodes

    def extend_episode(self, file, p_identifier):
        if not file:
            return []

        _, p_episode = p_identifier

        # Get just the name of the first part (without full path and extension)
        file_name = self.name(file)

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
            # Cast parameters to integers
            c_from = try_convert(c_identifier['episode_from'], int)
            c_to = try_convert(c_identifier['episode_to'], int)

            if c_from is None or c_to is None:
                return

            # Ensure range is valid
            count = c_to - c_from

            if count > 10 or count < 0:
                return

            # Ensure plex episode is inside identifier episode range
            if c_from <= p_episode <= c_to:
                c_episodes = range(c_from, c_to + 1)
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
