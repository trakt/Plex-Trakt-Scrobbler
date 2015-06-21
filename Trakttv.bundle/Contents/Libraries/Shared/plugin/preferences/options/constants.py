from plugin.core.enums import ActivityMode, MatcherMode

#
# Activity Mode
#

ACTIVITY_BY_KEY = {
    ActivityMode.Automatic:     'Automatic',
    ActivityMode.Logging:       'Logging (Legacy)',
    ActivityMode.WebSocket:     'WebSocket (PlexPass)'
}

ACTIVITY_BY_LABEL = {
    'Automatic':            ActivityMode.Automatic,
    'Logging (Legacy)':     ActivityMode.Logging,
    'WebSocket (PlexPass)': ActivityMode.WebSocket
}

#
# Matcher Mode
#

MATCHER_BY_KEY = {
    MatcherMode.Plex:           'Plex',
    MatcherMode.PlexExtended:   'Plex Extended'
}

MATCHER_BY_LABEL = {
    'Plex':             MatcherMode.Plex,
    'Plex Extended':    MatcherMode.PlexExtended
}
