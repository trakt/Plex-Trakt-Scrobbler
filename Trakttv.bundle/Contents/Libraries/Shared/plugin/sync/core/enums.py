class SyncActionMode(object):
    Update  = 0x00
    Log     = 0x01

class SyncConflictResolution(object):
    Latest  = 0x00
    Trakt   = 0x01
    Plex    = 0x02


class SyncData(object):
    All         = 0x00
    Collection  = 0x01
    Playback    = 0x02
    Ratings     = 0x04
    Watched     = 0x08
    Watchlist   = 0x16

    __titles__ = None

    @classmethod
    def title(cls, value):
        if cls.__titles__ is None:
            # Build titles map
            cls.__titles__ = {
                cls.All:           'All',
                cls.Collection:    'Collection',
                cls.Playback:      'Playback',
                cls.Ratings:       'Ratings',
                cls.Watched:       'Watched',
                cls.Watchlist:     'Watchlist'
            }

        return cls.__titles__.get(value)


class SyncMedia(object):
    All         = 0x00
    Movies      = 0x01
    Shows       = 0x02
    Seasons     = 0x04
    Episodes    = 0x08

    __titles__ = None

    @classmethod
    def title(cls, value):
        if cls.__titles__ is None:
            # Build titles map
            cls.__titles__ = {
                cls.All:        'All',
                cls.Movies:     'Movies',
                cls.Shows:      'Shows',
                cls.Seasons:    'Seasons',
                cls.Episodes:   'Episodes',
            }

        return cls.__titles__.get(value)


class SyncMode(object):
    Full        = 0x00
    Pull        = 0x01
    Push        = 0x02
    FastPull    = 0x04

    __titles__ = None

    @classmethod
    def title(cls, value):
        if cls.__titles__ is None:
            # Build titles map
            cls.__titles__ = {
                cls.Full:       'Full',
                cls.Pull:       'Pull',
                cls.Push:       'Push',
                cls.FastPull:   'Quick Pull'
            }

        return cls.__titles__.get(value)
