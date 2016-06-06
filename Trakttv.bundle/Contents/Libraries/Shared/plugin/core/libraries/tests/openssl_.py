from plugin.core.libraries.tests.core.base import BaseTest


class OpenSSL(BaseTest):
    name = 'openssl'
    optional = True

    @staticmethod
    def test_import():
        import OpenSSL.SSL

        # Try construct SSL context
        ctx = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)

        # Inject pyopenssl into requests
        from requests.packages.urllib3.contrib.pyopenssl import inject_into_urllib3
        inject_into_urllib3()

        return {
            'versions': {
                'pyopenssl': getattr(OpenSSL, '__version__', None)
            }
        }

    @classmethod
    def on_success(cls, metadata):
        from plugin.core.logger.handlers.error_reporter import RAVEN

        # Enable secure error reporting
        RAVEN.set_protocol('threaded+requests+https')
