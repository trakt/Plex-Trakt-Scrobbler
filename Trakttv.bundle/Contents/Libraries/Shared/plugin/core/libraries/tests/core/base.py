from plugin.core.helpers.variable import merge

import sys


class TestBase(object):
    name = None
    optional = False

    @classmethod
    def run(cls):
        metadata = {}

        # Retrieve names of test functions
        names = [
            name for name in dir(cls)
            if name.startswith('test_')
        ]

        if not names:
            return cls.on_failure('No tests defined')

        # Run tests
        for name in names:
            # Retrieve function by name
            func = getattr(cls, name, None)

            if not func:
                return cls.on_failure('Unable to find function: %r' % name)

            try:
                # Run test function
                result = func()

                if not result:
                    continue

                # Merge function result into `metadata`
                merge(metadata, result, recursive=True)
            except Exception, ex:
                return cls.on_exception('Exception raised in %r: %s' % (name, ex))

        # Tests successful
        return cls.on_success(metadata)

    #
    # Events
    #

    @classmethod
    def on_exception(cls, message, exc_info=None):
        if exc_info is None:
            exc_info = sys.exc_info()

        return cls.on_failure(
            message,
            exc_info=exc_info
        )

    @classmethod
    def on_failure(cls, message, **kwargs):
        result = {
            'success': False,
            'message': message
        }

        # Merge extra attributes
        merge(result, kwargs)

        return result

    @staticmethod
    def on_success(metadata):
        return {
            'success': True,
            'metadata': metadata
        }
