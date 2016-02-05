from plugin.core.libraries.tests.core.base import TestBase


class LList(TestBase):
    name = 'llist'
    optional = True

    @staticmethod
    def test_import():
        import llist
