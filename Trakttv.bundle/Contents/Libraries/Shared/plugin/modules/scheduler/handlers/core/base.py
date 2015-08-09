class Handler(object):
    key = None
    scope = 'account'

    def run(self, job):
        raise NotImplementedError
