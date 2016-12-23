class DisabledError(Exception):
    def __init__(self, message, inner_exception=None):
        super(DisabledError, self).__init__(message)

        self.inner_exception = inner_exception


class DatabaseDisabledError(DisabledError):
    def __init__(self, inner_exception=None):
        super(DatabaseDisabledError, self).__init__(
            'Database has been automatically disabled, check the plugin logs for more information',
            inner_exception
        )


class ModuleDisabledError(DisabledError):
    def __init__(self, inner_exception=None):
        super(ModuleDisabledError, self).__init__(
            'Module has been automatically disabled, check the plugin logs for more information',
            inner_exception
        )
