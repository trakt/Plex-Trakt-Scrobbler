from plugin.core.libraries.tests.core.base import BaseTest
# from plugin.core.logger.handlers.error_reporter import RAVEN


class OpenSSL(BaseTest):
    name = 'openssl'
    optional = True

    @staticmethod
    def test_import():
        import OpenSSL

        # Inject pyopenssl into requests
        from requests.packages.urllib3.contrib.pyopenssl import inject_into_urllib3
        inject_into_urllib3()

        # Enable secure error reporting
        # RAVEN.set_protocol('threaded+requests+https')

        return {
            'versions': {
                'pyopenssl': getattr(OpenSSL, '__version__', None)
            }
        }
