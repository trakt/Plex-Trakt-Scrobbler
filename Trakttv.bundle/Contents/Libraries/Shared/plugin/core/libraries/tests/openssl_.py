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
        standard_sslwrap = cls._standard_has_sslwrap()

        bundled_version = cls._bundled_version()

        libraries = {
            'standard': {
                'version': standard_version,
                'contexts': standard_contexts,
                'sslwrap': standard_sslwrap
            },

            'bundled': {
                'version': bundled_version
            }
        }

        # Check if we should use the standard ssl library
        if cls._use_standard(libraries):
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
        elif not libraries['standard']['sslwrap']:
            log.debug('Standard SSL library doesn\'t support "sslwrap"')
        elif libraries['bundled']['version'] > libraries['standard']['version']:
            log.debug('Standard SSL library is out of date')

        # Initialize ssl library
        if metadata['type'] == 'bundled':
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

    #
    # Helpers
    #

    @classmethod
    def _use_standard(cls, libraries):
        if not libraries['standard']['contexts']:
            return False

        if not libraries['standard']['sslwrap']:
            return False

        # Ensure bundled library is available
        if libraries['bundled']['version'] is None:
            return True

        # Compare standard library versions
        if libraries['standard']['version'] is None:
            return False

        return libraries['standard']['version'] > libraries['bundled']['version']

    @classmethod
    def _standard_has_contexts(cls):
        try:
            import ssl
            import _ssl

            return hasattr(ssl, 'SSLContext') and hasattr(_ssl, '_SSLContext')
        except Exception as ex:
            log.warn('Unable to check if the standard ssl library supports "SSLContext": %s', ex, exc_info=True)

        return None

    @classmethod
    def _standard_has_sslwrap(cls):
        try:
            import _ssl

            return hasattr(_ssl, 'sslwrap') or hasattr(_ssl._SSLContext, '_wrap_socket')
        except Exception as ex:
            log.warn('Unable to check if the standard ssl library supports "sslwrap": %s', ex, exc_info=True)

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
