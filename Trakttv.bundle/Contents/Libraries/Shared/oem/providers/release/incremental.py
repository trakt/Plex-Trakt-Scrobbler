from oem.providers.release.core.base import ReleaseProvider

from semantic_version import Version
import logging
import requests
import urlparse

log = logging.getLogger(__name__)


class IncrementalReleaseProvider(ReleaseProvider):
    def fetch(self, source, target, key, metadata):
        version = self.storage.get_collection_version(source, target)

        # Update item
        if not self.update_item(source, target, version, key, metadata):
            return False

        return True

    def get_available_version(self, source, target):
        # TODO Retrieve latest version available
        return Version('1.0.0')

    #
    # Update methods
    #

    def update_database(self, source, target):
        # Retrieve available version for collection
        available = self.get_available_version(source, target)

        # Update index
        if not self.update_index(source, target, available):
            return False

        return True

    def update_index(self, source, target, version, force=False):
        current_version = self.storage.get_collection_version(source, target)

        if current_version is not None and current_version >= version and not force:
            log.info('[%s -> %s] Collection is up to date (v%s)', source, target, current_version)
            return True

        log.info('[%s -> %s] Updating collection to v%s', source, target, version)
    
        # Fetch index
        response = self._fetch(source, target, version, 'index.%s' % self.format.__extension__)

        if response is None:
            return False
    
        # Update cache
        if not self.storage.update_index(source, target, response):
            return False

        # Update collection
        if not self.storage.update_collection(source, target, version):
            return False

        log.info('[%s -> %s] Collection has been updated to v%s', source, target, version)
        return True

    def update_item(self, source, target, version, key, metadata):
        if self.storage.has_item(source, target, key):
            return True
    
        # Fetch index
        response = self._fetch(source, target, version, '/'.join([
            'items',
            '%s.%s' % (key, self.format.__extension__)
        ]))
    
        # Update cache
        return self.storage.update_item(source, target, key, response, metadata)

    #
    # Private methods
    #

    def _fetch(self, source, target, version, filename):
        # Build URL
        url = self._build_url(source, target, version, filename)

        if url is None:
            return None

        # Fetch file
        try:
            response = requests.get(url, stream=True)
        except requests.ConnectionError, ex:
            log.warn('Unable to fetch file %r - %s', filename, ex)
            return None

        if response.status_code != 200:
            return None

        return response

    def _build_url(self, source, target, version, path):
        if self.database_url is None:
            return None

        return urlparse.urljoin(
            self.database_url,
            '/'.join([
                self._client.package_name(source, target),
                str(version),
                self._client.database_name(source, target),
                source,
                path
            ])
        )
