from plugin.core.libraries.tests.core.base import BaseTest


class Cryptography(BaseTest):
    name = 'cryptography'
    optional = True

    @staticmethod
    def test_import():
        import cryptography.hazmat.bindings.openssl.binding

        return {
            'versions': {
                'cryptography': getattr(cryptography, '__version__', None)
            }
        }
