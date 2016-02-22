AGENTS = {
    'local': {},

    #
    # Anime
    #

    'com.plexapp.agents.anidb': {
        'media': ['show', 'season', 'episode'],

        'service': 'anidb',
        'type': int
    },

    'com.plexapp.agents.hama': {
        'media': ['show', 'season', 'episode'],

        'children': [
            {'pattern': r'anidb-(.*)', 'service': 'anidb', 'type': int},
            {'pattern': r'tmdb-(.*)',  'service': 'tmdb',  'type': int},
            {'pattern': r'tvdb-(.*)',  'service': 'tvdb',  'type': int},
            {'pattern': r'imdb-(.*)',  'service': 'imdb'}
        ]
    },

    'net.fribbtastic.coding.plex.myanimelist': {
        'media': ['show', 'season', 'episode'],

        'service': 'myanimelist',
        'type': int
    },

    #
    # TV Shows
    #

    'com.plexapp.agents.abstvdb': {
        'media': ['show', 'season', 'episode'],

        'service': 'tvdb',
        'type': int
    },

    'com.plexapp.agents.mcm': {
        'media': ['show', 'season', 'episode'],

        'pattern': r'MCM_TV_A_(.*)',
        'service': 'tvdb',
        'type': int
    },

    'com.plexapp.agents.thetvdb': {
        'media': ['show', 'season', 'episode'],

        'service': 'tvdb',
        'type': int
    },

    'com.plexapp.agents.thetvdbdvdorder': {
        'media': ['show', 'season', 'episode'],

        'service': 'tvdb',
        'type': int
    },

    'com.plexapp.agents.xbmcnfotv': {
        'media': ['show', 'season', 'episode'],

        'children': [
            {'pattern': r'(tt\d+)', 'service': 'imdb'}
        ],
        'service': 'tvdb',
        'type': int
    },

    #
    # Movies
    #

    'com.plexapp.agents.standalone': {
        'media': ['movie'],

        'service': 'tmdb',
        'type': int
    },

    'com.plexapp.agents.xbmcnfo': {
        'media': ['movie'],

        'service': 'imdb'
    },

    #
    # Multi
    #

    'com.plexapp.agents.imdb': {
        'service': 'imdb'
    },

    'com.plexapp.agents.themoviedb': {
        'service': 'tmdb',
        'type': int
    }
}
