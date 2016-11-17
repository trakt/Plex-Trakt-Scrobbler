class ModuleDisabledError(Exception):
    def __init__(self, inner_exception):
        super(ModuleDisabledError, self).__init__(
            'Module has been automatically disabled, check the plugin logs for more information'
        )

        self.inner_exception = inner_exception
