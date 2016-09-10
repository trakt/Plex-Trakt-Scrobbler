DATABASES = {
    ('anidb', 'imdb'): 'oem_database_anidb_imdb',
    ('imdb', 'anidb'): 'oem_database_anidb_imdb',

    ('anidb', 'tmdb:movie'): 'oem_database_anidb_tmdb_movie',
    ('tmdb:movie', 'anidb'): 'oem_database_anidb_tmdb_movie',

    ('anidb', 'tmdb:show'): 'oem_database_anidb_tmdb_show',
    ('tmdb:show', 'anidb'): 'oem_database_anidb_tmdb_show',

    ('anidb', 'tvdb'): 'oem_database_anidb_tvdb',
    ('tvdb', 'anidb'): 'oem_database_anidb_tvdb',
}

PACKAGES = {
    ('anidb', 'imdb'): 'oem-database-anidb-imdb',
    ('imdb', 'anidb'): 'oem-database-anidb-imdb',

    ('anidb', 'tmdb:movie'): 'oem-database-anidb-tmdb-movie',
    ('tmdb:movie', 'anidb'): 'oem-database-anidb-tmdb-movie',

    ('anidb', 'tmdb:show'): 'oem-database-anidb-tmdb-show',
    ('tmdb:show', 'anidb'): 'oem-database-anidb-tmdb-show',

    ('anidb', 'tvdb'): 'oem-database-anidb-tvdb',
    ('tvdb', 'anidb'): 'oem-database-anidb-tvdb',
}

SERVICES = {
    'anidb': [
        'imdb',
        'tmdb:movie',
        'tmdb:show',
        'tvdb'
    ],

    'imdb': [
        'anidb'
    ],

    'tmdb:movie': [
        'anidb'
    ],

    'tmdb:show': [
        'anidb'
    ],

    'tvdb': [
        'anidb'
    ]
}
