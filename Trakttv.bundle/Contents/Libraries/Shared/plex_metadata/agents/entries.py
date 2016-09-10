AGENTS = {
    'com.plexapp.agents.none': {
        'service': 'none'
    },

    #
    # Local Media
    #

    'local': {},

    'com.arendshome.plex.agents.personalmedia': {
        'service': 'plex'
    },

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
            {'pattern': r'(\d+)',      'service': 'anidb',          'type': int},
            {'pattern': r'anidb-(.*)', 'service': 'anidb',          'type': int},
            {'pattern': r'tmdb-(.*)',  'service': 'tmdb',           'type': int},
            {'pattern': r'tvdb-(.*)',  'service': 'tvdb',           'type': int},
            {'pattern': r'imdb-(.*)',  'service': 'imdb'},

            # Hybrid identifiers
            {'pattern': r'tvdb2-(.*)',  'service': 'tvdb',          'type': int},
            {'pattern': r'tvdb3-(.*)',  'service': 'hama/tvdb3',    'type': int, 'season': 1},
        ]
    },

    'net.devvsbugs.coding.plex.myanimelist': {
        'media': ['show', 'season', 'episode'],

        'service': 'myanimelist',
        'type': int
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

    'com.plexapp.agents.kinopoiskrushow': {
        'media': ['show', 'season', 'episode'],

        'service': 'kinopoisk',
        'type': int
    },

    'com.plexapp.agents.mcm': {
        'media': ['show', 'season', 'episode'],

        'children': [
            {'pattern': r'MCM_TV_A_(.*)', 'service': 'tvdb', 'type': int}
        ],
        'service': 'mcm'
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

    'com.plexapp.agents.AlloCine': {
        'media': ['movie'],

        'service': 'allocine',
        'type': int
    },

    'com.plexapp.agents.cinepassion': {
        'media': ['movie'],

        'service': 'cinepassion',
        'type': int
    },

    'com.plexapp.agents.filmaffinity': {
        'media': ['movie'],

        'service': 'filmaffinity',
        'type': int
    },

    'com.plexapp.agents.kinopoisk': {
        'media': ['movie'],

        'service': 'kinopoisk',
        'type': int
    },

    'com.plexapp.agents.kinopoiskru': {
        'media': ['movie'],

        'service': 'kinopoisk',
        'type': int
    },

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
    },

    #
    # Misc
    #

    'com.plexapp.agents.youtube': {
        'service': 'youtube'
    }
}
