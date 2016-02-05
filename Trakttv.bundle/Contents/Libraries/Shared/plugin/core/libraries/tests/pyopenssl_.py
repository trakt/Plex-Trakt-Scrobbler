from plugin.core.libraries.tests.core.base import TestBase


class PyOpenSSL(TestBase):
    name = 'pyopenssl'
    optional = True

    @staticmethod
    def test_import():
        import OpenSSL

        # Inject pyopenssl into requests
        from requests.packages.urllib3.contrib.pyopenssl import inject_into_urllib3
        inject_into_urllib3()

        return {
            'versions': {
                'pyopenssl': getattr(OpenSSL, '__version__', None)
            }
        }
