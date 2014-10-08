DEFAULT_TYPES = ['movie', 'show', 'episode']

DEFAULT_GUID_MAP = {
    # Multi
    'mcm':              ('thetvdb', r'MCM_TV_A_(.*)'),

    # Movie
    'xbmcnfo':          'imdb',
    'standalone':       'themoviedb',

    # TV
    'abstvdb':          'thetvdb',
    'thetvdbdvdorder':  'thetvdb',
    'xbmcnfotv':        [
        ('imdb', r'(tt\d+)'),
        'thetvdb'
    ],
}

DEFAULT_TV_AGENTS = [
    'com.plexapp.agents.thetvdb',
    'com.plexapp.agents.thetvdbdvdorder',
    'com.plexapp.agents.abstvdb',
    'com.plexapp.agents.xbmcnfotv',
    'com.plexapp.agents.mcm'
]
