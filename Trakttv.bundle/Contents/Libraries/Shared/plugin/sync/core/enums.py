class SyncData(object):
    All         = 0x00
    Collection  = 0x01
    Playback    = 0x02
    Ratings     = 0x04
    Watched     = 0x08
    Watchlist   = 0x16


class SyncMedia(object):
    All         = 0x00
    Movies      = 0x01
    Shows       = 0x02
    Seasons     = 0x04
    Episodes    = 0x08


class SyncMode(object):
    Full        = 0x00

    Pull        = 0x01
    Push        = 0x02

    FastPull    = 0x04
