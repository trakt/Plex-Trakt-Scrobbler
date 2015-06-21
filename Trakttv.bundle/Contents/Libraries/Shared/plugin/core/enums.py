class ActivityMode(object):
    Automatic       = None
    Logging         = 0x00
    WebSocket       = 0x01


class ConflictResolution(object):
    Latest  = 0x00
    Trakt   = 0x01
    Plex    = 0x02


class MatcherMode(object):
    Plex            = 0x00
    PlexExtended    = 0x01
