from plugin.core.enums import ActivityMode, MatcherMode

#
# Activity Mode
#

ACTIVITY_IDS_BY_KEY = {
    ActivityMode.Automatic:     0,
    ActivityMode.Logging:       1,
    ActivityMode.WebSocket:     2
}

ACTIVITY_KEYS_BY_LABEL = {
    'Automatic':            ActivityMode.Automatic,
    'Logging (Legacy)':     ActivityMode.Logging,
    'WebSocket (PlexPass)': ActivityMode.WebSocket
}

ACTIVITY_LABELS_BY_KEY = {
    ActivityMode.Automatic:     'Automatic',
    ActivityMode.Logging:       'Logging (Legacy)',
    ActivityMode.WebSocket:     'WebSocket (PlexPass)'
}

#
# Matcher Mode
#

MATCHER_IDS_BY_KEY = {
    MatcherMode.Plex:           0,
    MatcherMode.PlexExtended:   1
}

MATCHER_KEYS_BY_LABEL = {
    'Plex':             MatcherMode.Plex,
    'Plex Extended':    MatcherMode.PlexExtended
}

MATCHER_LABELS_BY_KEY = {
    MatcherMode.Plex:           'Plex',
    MatcherMode.PlexExtended:   'Plex Extended'
}
