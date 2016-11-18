from exception_wrappers import DisabledError


class AccountAuthenticationError(Exception):
    pass


class PluginDisabledError(DisabledError):
    def __init__(self, inner_exception=None):
        super(PluginDisabledError, self).__init__(
            'Plugin has been automatically disabled, check the plugin logs for more information',
            inner_exception
        )
