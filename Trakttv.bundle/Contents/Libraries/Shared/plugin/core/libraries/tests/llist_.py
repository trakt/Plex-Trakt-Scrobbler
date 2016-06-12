from plugin.core.libraries.tests.core.base import BaseTest


class LList(BaseTest):
    name = 'llist'
    optional = True

    @staticmethod
    def test_import():
        import llist
