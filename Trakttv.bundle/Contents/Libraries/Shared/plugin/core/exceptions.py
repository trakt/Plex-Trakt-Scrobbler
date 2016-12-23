from exception_wrappers import DisabledError


class AccountAuthenticationError(Exception):
    pass


class ConnectionError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return '%s: %s' % (
            self.__class__.__name__,
            self.message
        )

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self.message
        )


class PluginDisabledError(DisabledError):
    def __init__(self, inner_exception=None):
        super(PluginDisabledError, self).__init__(
            'Plugin has been automatically disabled, check the plugin logs for more information',
            inner_exception
        )
