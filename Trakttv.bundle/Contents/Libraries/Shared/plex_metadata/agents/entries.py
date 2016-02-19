AGENTS = {
    'local': {},

    #
    # Anime
    #

    'com.plexapp.agents.anidb': {
        'media': ['show', 'season', 'episode'],

        'service': 'anidb'
    },

    'com.plexapp.agents.hama': {
        'media': ['show', 'season', 'episode'],

        'children': [
            {'pattern': r'anidb-(.*)', 'service': 'anidb'},
            {'pattern': r'imdb-(.*)', 'service': 'imdb'},
            {'pattern': r'tmdb-(.*)', 'service': 'tmdb'},
            {'pattern': r'tvdb-(.*)', 'service': 'tvdb'}
        ]
    },

    'net.fribbtastic.coding.plex.myanimelist': {
        'media': ['show', 'season', 'episode'],

        'service': 'myanimelist'
    },

    #
    # TV Shows
    #

    'com.plexapp.agents.abstvdb': {
        'media': ['show', 'season', 'episode'],

        'service': 'tvdb'
    },

    'com.plexapp.agents.mcm': {
        'media': ['show', 'season', 'episode'],

        'pattern': r'MCM_TV_A_(.*)',
        'service': 'tvdb'
    },

    'com.plexapp.agents.thetvdb': {
        'media': ['show', 'season', 'episode'],

        'service': 'tvdb'
    },

    'com.plexapp.agents.thetvdbdvdorder': {
        'media': ['show', 'season', 'episode'],

        'service': 'tvdb'
    },

    'com.plexapp.agents.xbmcnfotv': {
        'media': ['show', 'season', 'episode'],

        'children': [
            {'pattern': r'(tt\d+)', 'service': 'imdb'}
        ],
        'service': 'tvdb'
    },

    #
    # Movies
    #

    'com.plexapp.agents.standalone': {
        'media': ['movie'],

        'service': 'tmdb'
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
        'service': 'tmdb'
    }
}
