DEFAULT_TYPES = ['movie', 'show', 'season', 'episode']

DEFAULT_GUID_MAP = {
    # Multi
    'mcm':              ('tvdb', r'MCM_TV_A_(.*)'),

    # Movie
    'standalone':       'tmdb',
    'themoviedb':       'tmdb',
    'xbmcnfo':          'imdb',

    # TV
    'abstvdb':          'tvdb',
    'thetvdb':          'tvdb',
    'thetvdbdvdorder':  'tvdb',
    'xbmcnfotv':        [
        ('imdb', r'(tt\d+)'),
        'tvdb'
    ],
}

DEFAULT_TV_AGENTS = [
    'com.plexapp.agents.thetvdb',
    'com.plexapp.agents.thetvdbdvdorder',
    'com.plexapp.agents.abstvdb',
    'com.plexapp.agents.xbmcnfotv',
    'com.plexapp.agents.mcm'
]
