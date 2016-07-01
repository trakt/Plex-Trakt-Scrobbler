from plugin.core.libraries.tests.core.base import BaseTest

import logging

log = logging.getLogger(__name__)


class OpenSSL(BaseTest):
    name = 'openssl'
    optional = True

    @staticmethod
    def test_import():
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

        return {
            'versions': {
                'pyopenssl': getattr(OpenSSL, '__version__', None)
            }
        }

    @classmethod
    def on_success(cls, metadata):
        # Inject pyOpenSSL into requests
        try:
            from requests.packages.urllib3.contrib.pyopenssl import inject_into_urllib3
            inject_into_urllib3()
        except Exception, ex:
            log.warn('Unable to inject pyOpenSSL into urllib3 - %s', ex, exc_info=True)
            return

        # Enable secure error reporting
        from plugin.core.logger.handlers.error_reporter import RAVEN
        RAVEN.set_protocol('threaded+requests+https')
