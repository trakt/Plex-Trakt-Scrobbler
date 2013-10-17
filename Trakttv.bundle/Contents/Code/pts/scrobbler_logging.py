from pts.scrobbler import Scrobbler


class LoggingScrobbler(Scrobbler):
    def update(self, info):
        Log.Info('[LoggingScrobbler](update) info: %s' % info)
