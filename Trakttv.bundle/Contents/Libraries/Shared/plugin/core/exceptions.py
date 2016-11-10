class AccountAuthenticationError(Exception):
    pass


class PluginDisabledError(Exception):
    def __init__(self):
        super(PluginDisabledError, self).__init__(
            'Plugin has been automatically disabled, check the plugin logs for more information'
        )
