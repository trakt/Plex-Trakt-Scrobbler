from plugin.core.libraries.tests.core.base import BaseTest


class Apsw(BaseTest):
    name = 'apsw'

    @staticmethod
    def test_import():
        import apsw

        return {
            'versions': {
                'apsw': apsw.apswversion(),
                'sqlite': apsw.SQLITE_VERSION_NUMBER
            }
        }
