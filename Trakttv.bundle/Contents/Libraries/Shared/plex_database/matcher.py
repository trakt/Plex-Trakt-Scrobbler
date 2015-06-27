import plex_metadata.matcher
import logging

log = logging.getLogger(__name__)


class Matcher(plex_metadata.matcher.Matcher):
    def process(self, metadata):
        raise NotImplementedError

    def process_episode(self, id, identifier, file):
        # Get plex identifier
        p_season, p_episode = identifier

        # Ensure plex identifier is valid
        if p_season is None or p_episode is None:
            log.debug('Ignoring item with key "%s", invalid season or episode attribute', id)
            return None, []

        # Find new episodes from identifiers
        c_episodes = [p_episode]

        if file and self._extend_enabled:
            # Add extended episodes
            c_episodes.extend(self.extend_episode(file, identifier))

            # Remove any episode identifiers that are more than 1 away
            c_episodes = self.remove_distant(c_episodes, p_episode)
        elif self._extend_enabled:
            log.warn('Item with key "%s" has no media parts, unable to use the extended matcher', id)

        return p_season, c_episodes

# Global object
Default = Matcher()
