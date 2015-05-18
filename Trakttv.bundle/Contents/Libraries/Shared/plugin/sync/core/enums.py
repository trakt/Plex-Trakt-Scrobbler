class SyncAction(object):
    Both        = 0

    Pull        = 1
    Push        = 2


class SyncData(object):
    All         = 0

    Collection  = 1
    Playback    = 2
    Ratings     = 4
    Watched     = 8
