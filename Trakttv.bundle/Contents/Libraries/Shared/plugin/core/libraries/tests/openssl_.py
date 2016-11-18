from plugin.core.libraries.tests.core.base import BaseTest

import logging

log = logging.getLogger(__name__)


class OpenSSL(BaseTest):
    name = 'openssl'
    optional = True

    @classmethod
    def test_import(cls):
        standard_version = cls._standard_version()
        standard_contexts = cls._standard_has_contexts()

        bundled_version = cls._bundled_version()

        libraries = {
            'standard': {
                'version': standard_version,
                'contexts': standard_contexts
            },

            'bundled': {
                'version': bundled_version
            }
        }

        # Check if we should use the standard ssl library
        if standard_contexts and (bundled_version is None or (standard_version and standard_version > bundled_version)):
            return {
                'type': 'standard',
                'libraries': libraries,

                'versions': {
                    'openssl': standard_version
                }
            }

        # Test pyOpenSSL availability
        import OpenSSL.SSL

        # Try construct SSL context
        ctx = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)

        # Ensure library has SNI support
        cnx = OpenSSL.SSL.Connection(ctx)

        if not hasattr(cnx, 'set_tlsext_host_name'):
            raise Exception('Missing SNI extension')

        # Ensure binding can be imported
        from cryptography.hazmat.bindings.openssl.binding import Binding
        assert Binding

        # Ensure secure connections work with requests
        from requests.packages.urllib3.contrib.pyopenssl import inject_into_urllib3
        import requests

        inject_into_urllib3()

        try:
            requests.head('https://api-v2launch.trakt.tv', timeout=3)
        except requests.RequestException as ex:
            # Ignore failed requests (server error, network problem, etc..)
            log.warn('Request failed: %s', ex, exc_info=True)

        return {
            'type': 'bundled',
            'libraries': libraries,

            'versions': {
                'openssl': bundled_version,
                'pyopenssl': getattr(OpenSSL, '__version__', None)
            }
        }

    @classmethod
    def on_success(cls, metadata):
        libraries = metadata['libraries']

        if not libraries['standard']['contexts']:
            log.debug('Standard SSL library doesn\'t support "SSLContext"')

        # Initialize ssl library
        if metadata['type'] == 'bundled':
            if libraries['bundled']['version'] > libraries['standard']['version']:
                log.debug('Standard SSL library is out of date')

            # Inject pyOpenSSL into requests
            log.debug('Using bundled SSL library (pyOpenSSL)')

            try:
                from requests.packages.urllib3.contrib.pyopenssl import inject_into_urllib3
                inject_into_urllib3()
            except Exception as ex:
                log.warn('Unable to inject pyOpenSSL into urllib3 - %s', ex, exc_info=True)
                return
        else:
            log.debug('Using standard SSL library (ssl)')

        # Enable secure error reporting
        from plugin.core.logger.handlers.error_reporter import RAVEN
        RAVEN.set_protocol('threaded+requests+https')

    #
    # Helpers
    #

    @classmethod
    def _standard_has_contexts(cls):
        try:
            import ssl
            return hasattr(ssl, 'SSLContext')
        except Exception as ex:
            log.warn('Unable to check if the standard ssl library supports "SSLContext": %s', ex, exc_info=True)

        return None

    @classmethod
    def _standard_version(cls):
        try:
            import ssl
            return ssl.OPENSSL_VERSION_NUMBER
        except Exception as ex:
            log.warn('Unable to retrieve standard ssl library version: %s', ex, exc_info=True)

        return None

    @classmethod
    def _bundled_version(cls):
        try:
            from cryptography.hazmat.bindings.openssl.binding import Binding
            return Binding.lib.SSLeay()
        except Exception as ex:
            log.warn('Unable to retrieve bundled ssl library version: %s', ex, exc_info=True)

        return None
