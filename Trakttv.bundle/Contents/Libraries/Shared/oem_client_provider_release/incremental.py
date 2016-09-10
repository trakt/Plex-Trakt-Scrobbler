# flake8: noqa

from oem_client_provider_release.core.base import ReleaseProvider

from semantic_version import Version
from six.moves.urllib.parse import urlparse, urljoin
import logging
import requests
import time

log = logging.getLogger(__name__)

UPDATE_CHECK_INTERVAL   = 12 * 60 * 60  # Check for updates every 12 hours
UPDATE_RETRY_INTERVAL   =  1 * 60 * 60  # Retry unavailable (404) versions every hour


class IncrementalReleaseProvider(ReleaseProvider):
    __key__ = 'release/incremental'

    def __init__(self, *args, **kwargs):
        super(IncrementalReleaseProvider, self).__init__(*args, **kwargs)

        self._client_version = None

        self._database_latest_version = {}
        self._database_unavailable = {}

        self._version_disabled = {}
        self._version_unavailable = {}

    def initialize(self, client):
        super(IncrementalReleaseProvider, self).initialize(client)

        self._client_version = Version(client.version)

    def fetch(self, source, target, key, metadata):
        version = self.get_available_version(source, target)

        # Update item
        if not self.update_item(source, target, version, key, metadata):
            return False

        return True

    def get_available_version(self, source, target):
        if not self.database_author:
            return None

        repo = '%s/%s' % (
            self.database_author,
            self._client.package_name(source, target)
        )

        # Retrieve version from cache
        item = self._database_latest_version.get(repo)

        if item:
            last_check = time.time() - item['updated_at']

            if last_check < UPDATE_CHECK_INTERVAL:
                return item['version']

        # Check if database is unavailable
        unavailable_at = self._database_unavailable.get(repo)

        if unavailable_at:
            last_error = time.time() - unavailable_at

            if last_error < UPDATE_RETRY_INTERVAL:
                log.debug(
                    'Database %r is unavailable, will retry in %d seconds',
                    repo, UPDATE_RETRY_INTERVAL - last_error
                )
                return None

        # Retrieve latest release information
        try:
            response = requests.get('https://api.github.com/repos/%s/releases/latest' % repo)
        except requests.ConnectionError as ex:
            log.warn('Unable to fetch release information for %r - %s', repo, ex)
            return None

        if response.status_code < 200 or response.status_code >= 300:
            log.info('Unable to find database %r, will retry in %d seconds', repo, UPDATE_RETRY_INTERVAL)
            self._database_unavailable[repo] = time.time()
            return None

        data = response.json()

        if not data.get('tag_name'):
            log.warn('Invalid release returned for %r: %r', repo, data)
            return None

        # Cache version for future calls
        self._database_latest_version[repo] = {
            'version': Version(data['tag_name']),
            'updated_at': time.time()
        }

        # TODO Retrieve latest version available
        return self._database_latest_version[repo]['version']

    #
    # Update methods
    #

    def update_database(self, source, target):
        # Retrieve available version for collection
        available = self.get_available_version(source, target)

        if available is None:
            return False

        # Update index
        if not self.update_index(source, target, available):
            return False

        return True

    def update_index(self, source, target, version, force=False):
        current_version = self.storage.get_collection_version(source, target)

        if current_version is not None and current_version >= version and not force:
            log.info('[%s -> %s] Collection is up to date (v%s)', source, target, current_version)
            return True

        if (source, target, version) in self._version_disabled and not force:
            log.warn(
                '[%s -> %s] Update to v%s has been disabled: %s',
                source, target, version, self._version_disabled[(source, target, version)]
            )
            return False

        log.info('[%s -> %s] Updating collection to v%s', source, target, version)

        # Fetch package information
        version_details = self._fetch_version_details(source, target, version)

        if version_details is None:
            return False

        # Ensure package version is compatible with the client
        minimum_version = version_details.get('client', {}).get('minimum_version')

        if minimum_version and self._client_version < Version(minimum_version):
            reason = "oem-client needs to be updated to at least v%s" % minimum_version

            log.warn('[%s -> %s] Unable to update collection to v%s: %s', source, target, version, reason)
            self._version_disabled[(source, target, version)] = reason
            return False

        # Fetch index
        response = self._fetch(source, target, version, 'database:///index.%s' % self.format.__extension__)

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
        if self.storage.has_item(source, target, key, metadata):
            return True

        # Fetch item
        response = self._fetch(source, target, version, 'database:///%s' % '/'.join([
            'items',
            '%s.%s' % (key, self.format.__extension__)
        ]))

        if response is None:
            return False

        # Update cache
        return self.storage.update_item(source, target, key, response, metadata)

    #
    # Private methods
    #

    def _fetch_version_details(self, source, target, version):
        response = self._fetch(source, target, version, 'package:///package.json')

        if response is None:
            return None

        return response.json()

    def _fetch(self, source, target, version, uri):
        # Check if version is unavailable
        unavailable_at = self._version_unavailable.get((source, target, version))

        if unavailable_at:
            last_error = time.time() - unavailable_at

            if last_error < UPDATE_RETRY_INTERVAL:
                log.debug(
                    'Version %s is unavailable, will retry in %d seconds',
                    version, UPDATE_RETRY_INTERVAL - last_error
                )
                return None

        # Build URL
        url = self._build_url(source, target, version, uri)

        if url is None:
            return None

        # Fetch file
        try:
            response = requests.get(url)
        except requests.ConnectionError as ex:
            log.warn('Unable to fetch file %r - %s', uri, ex)
            return None

        if response.status_code < 200 or response.status_code >= 300:
            log.info('Unable to fetch version %s, will retry in %d seconds', version, UPDATE_RETRY_INTERVAL)
            self._version_unavailable[(source, target, version)] = time.time()
            return None

        return response

    def _build_url(self, source, target, version, uri):
        if self.database_url is None:
            return None

        # Parse URI
        p_uri = urlparse(uri)

        # Build path fragments
        parts = [
            self._client.package_name(source, target),
            str(version),
            self._client.database_name(source, target),
        ]

        if p_uri.scheme == 'database':
            parts.append(source)

        # Build URL
        return urljoin(
            self.database_url,
            '/'.join(parts + [
                p_uri.path.lstrip('/')
            ]),
        )
