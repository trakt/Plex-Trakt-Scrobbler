import logging

log = logging.getLogger(__name__)


def test_apsw():
    import apsw

    log.debug('apsw: available (v%s) [sqlite: %s]', apsw.apswversion(), apsw.SQLITE_VERSION_NUMBER)


def test_cryptography():
    import cryptography
    from cryptography.hazmat.bindings.openssl.binding import Binding

    cryptography_version = getattr(cryptography, '__version__', None)
    openssl_version = Binding.lib.SSLeay()

    log.debug('cryptography: available (v%s) [openssl: %s]', cryptography_version, openssl_version)


def test_llist():
    import llist

    log.debug('llist: available')


def test_openssl():
    import OpenSSL

    log.debug('pyopenssl: available (v%s)', getattr(OpenSSL, '__version__', None))
