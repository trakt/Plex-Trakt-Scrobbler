from core.helpers import try_convert, json_encode, json_decode, get_pref
from core.logger import Logger
from plex.plex_base import PlexBase
from caper import Caper
import os

log = Logger('plex.plex_matcher')


class PlexMatcher(PlexBase):
    current = None

    cache_pending = 0
    cache_key = 'matcher_cache'
    cache = None

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
            if abs(s[x] - s[x - step]) <= max_distance:
                result.append(s[x])
            else:
                break

        return result

    @classmethod
    def match_identifier(cls, p_season, p_episode, c_identifier):
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
    def create_cache(cls):
        cls.cache = {
            'version': Caper.version,
            'entries': {}
        }

        log.info('Created PlexMatcher cache (version: %s)', cls.cache['version'])

    @classmethod
    def load(cls):
        # Already loaded?
        if cls.cache is not None:
            return

        if Data.Exists(cls.cache_key):
            cls.cache = json_decode(Data.Load(cls.cache_key))

            if cls.cache['version'] != Caper.version:
                Data.Remove(cls.cache_key)
                cls.cache = None
                log.info('Caper version changed, reset matcher cache')

            log.info('Loaded PlexMatcher cache (version: %s)', cls.cache['version'])

        # Create cache if one doesn't exist or is invalid
        if cls.cache is None:
            cls.create_cache()

    @classmethod
    def save(cls, force=False):
        if cls.cache_pending < 1 and not force:
            return

        Data.Save(cls.cache_key, json_encode(cls.cache))
        log.info('Saved PlexMatcher cache (pending: %s, version: %s)', cls.cache_pending, cls.cache['version'])

        cls.cache_pending = 0

    @classmethod
    def lookup(cls, file_hash):
        cls.load()
        return cls.cache['entries'].get(file_hash)

    @classmethod
    def store(cls, file_hash, identifier):
        cls.cache['entries'][file_hash] = identifier
        cls.cache_pending = cls.cache_pending + 1

    @classmethod
    def parse(cls, file_name, use_cache=True):
        identifier = None

        file_hash = Hash.MD5(file_name)

        # Try lookup identifier in cache
        if use_cache:
            identifier = cls.lookup(file_hash)

        # Parse new file_name
        if identifier is None:
            # Parse file_name with Caper
            result = cls.get_parser().parse(file_name)

            chain = result.chains[0] if result.chains else None

            # Get best identifier match from result
            identifier = chain.info.get('identifier', []) if chain else []

            # Update cache
            cls.store(file_hash, identifier)

        return identifier

    @classmethod
    def get_extended(cls, video, p_season, p_episode):
        # Ensure extended matcher is enabled
        if get_pref('matcher') != 'plex_extended':
            return []

        # Parse filename for extra info
        parts = video.find('Media').findall('Part')
        if not parts:
            log.warn('Item "%s" has no parts', video.get('ratingKey'))
            return []

        # Get just the name of the first part (without full path and extension)
        file_name = os.path.splitext(os.path.basename(parts[0].get('file')))[0]

        # Parse file_name with caper (or get cached result)
        c_identifiers = cls.parse(file_name)

        result = []
        for c_identifier in c_identifiers:
            if 'season' not in c_identifier:
                continue

            episodes = cls.match_identifier(p_season, p_episode, c_identifier)
            if episodes is None:
                continue

            # Insert any new episodes found from identifier
            for episode in episodes:
                if episode == p_episode:
                    continue

                result.append(episode)

        return result

    @classmethod
    def get_identifier(cls, video):
        # Get plex identifier
        p_season = try_convert(video.get('parentIndex'), int)
        p_episode = try_convert(video.get('index'), int)

        # Ensure plex data is valid
        if p_season is None or p_episode is None:
            log.debug('Ignoring item with key "%s", invalid season or episode attribute', video.get('ratingKey'))
            return None, []

        # Find new episodes from identifiers
        c_episodes = [p_episode]

        # Add extended episodes
        c_episodes.extend(cls.get_extended(video, p_season, p_episode))

        # Remove any episode identifiers that are more than 1 away
        c_episodes = cls.remove_distant(c_episodes, p_episode)

        return p_season, c_episodes
