from plugin.core.libraries.tests.core.base import BaseTest


class Cryptography(BaseTest):
    name = 'cryptography'
    optional = True

    @staticmethod
    def test_import():
        import cryptography
        from cryptography.hazmat.bindings.openssl.binding import Binding

        return {
            'versions': {
                'cryptography': getattr(cryptography, '__version__', None),
                'openssl': Binding.lib.SSLeay()
            }
        }
