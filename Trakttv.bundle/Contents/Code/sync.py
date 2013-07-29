from pms import PMS_URL, TVSHOW1_REGEXP, PMS
from helpers import SyncDownString, SyncUpString
from trakt import Trakt


def parse_section(section):
    return (
        section.get('type', None),
        section.get('key', None),
        section.get('title', None)
    )


def itersections(types=('show', 'movie')):
    """Iterate over valid PMS sections of type 'show' or 'movie'"""
    for section in [parse_section(s) for s in PMS.get_sections()]:
        # Ensure fields exist
        if all(v is not None for v in section):
            section_type, key, title = section
            # Ensure section is of type 'show' or 'movie'
            if section_type in types:
                yield section_type, key, title


def finditems(subject, items, key):
    for item in items:
        if key in item and item[key] == subject[key]:
            yield item


def matches(subject, items, func):
    for item in items:
        if func(item) == subject:
            yield item



@route('/applications/trakttv/manuallysync')
def ManuallySync():
    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    oc = ObjectContainer(title2=L("Sync"))
    all_keys = []

    for _, key, title in itersections():
        oc.add(DirectoryObject(
            key=Callback(SyncSection, key=[key]),
            title='Sync items in "' + title + '" to Trakt.tv',
            summary='Sync your ' + SyncUpString() + ' in the "' + title +
                    '" section of your Plex library with your Trakt.tv account.',
            thumb=R("icon-sync_up.png")
        ))
        all_keys.append(key)

    if len(all_keys) > 1:
        oc.add(DirectoryObject(
            key=Callback(SyncSection, key=",".join(all_keys)),
            title='Sync items in ALL sections to Trakt.tv',
            summary='Sync your ' + SyncUpString() +
                    ' in all sections of your Plex library with your Trakt.tv account.',
            thumb=R("icon-sync_up.png")
        ))

    oc.add(DirectoryObject(
        key=Callback(ManuallyTrakt),
        title='Sync items from Trakt.tv',
        summary='Sync your ' + SyncDownString() + ' items on Trakt.tv with your Plex library.',
        thumb=R("icon-sync_down.png")
    ))

    return oc

@route('/applications/trakttv/syncplex')
def SyncPlex():
    if (Dict['Last_sync_up'] + Datetime.Delta(minutes=360)) > Datetime.Now():
        Log('Not enough time since last sync, breaking!')
    else:
        for (_, key, _) in itersections():
            SyncSection(key)

@route('/applications/trakttv/synctrakt')
def SyncTrakt():
    LAST_SYNC_DOWN = Dict['Last_sync_down']

    if (LAST_SYNC_DOWN + Datetime.Delta(minutes=360)) > Datetime.Now():
        Log('Not enough time since last sync, breaking!')
    else:
        ManuallyTrakt()


def pull_movie(watched, rated, video):
    # Pull metadata
    metadata = PMS.metadata(video.get('ratingKey'))
    if 'imdb_id' not in metadata:
        return

    # Sync watched
    if Prefs['sync_watched'] is True:
        for movie in finditems(metadata, watched, 'imdb_id'):
            Log('Found %s with id %s' % (metadata['title'], video.get('ratingKey')))
            if not PMS.scrobble(video):
                Log('The movie %s is already marked as seen in the library.' % metadata['title'])

    # Sync ratings
    if Prefs['sync_ratings'] is True:
        for movie in finditems(metadata, rated, 'imdb_id'):
            Log('Found %s with id %s' % (metadata['title'], video.get('ratingKey')))
            PMS.rate(video, movie['rating_advanced'])


def pull_show(watched, rated, directory, tvdb_id):
    # Sync watched
    if Prefs['sync_watched'] is True:
        for show in [x for x in watched if x['tvdb_id'] == tvdb_id]:
            Log('We have a match for %s' % show['title'])

            for episode in PMS.get_metadata_leaves(directory.get('ratingKey')).xpath('//Video'):
                season_num = int(episode.get('parentIndex'))
                episode_num = int(episode.get('index'))

                for season in matches(season_num, show['seasons'], lambda x: int(x['season'])):

                    if episode_num in season['episodes']:
                        Log('Marking %s episode %s with key: %s as seen.' % (
                            episode.get('grandparentTitle'), episode.get('title'), episode.get('ratingKey')))

                        if not PMS.scrobble(episode):
                            Log('The episode %s is already marked as seen in the library.' % episode.get('title'))
    # Sync ratings
    if Prefs['sync_ratings'] is True:
        for show in [x for x in rated if rated['show']['tvdb_id'] == tvdb_id]:
            show_season = int(show['episode']['season'])
            show_episode = int(show['episode']['number'])

            for episode in PMS.get_metadata_leaves(directory.get('ratingKey')).xpath('//Video'):
                if show_season == int(episode.get('parentIndex')) and show_episode == int(episode.get('index')):
                    PMS.rate(episode, show['rating_advanced'])


@route('/applications/trakttv/manuallytrakt')
def ManuallyTrakt():

    if Prefs['username'] is None:
        Log('You need to enter you login information first.')
        return MessageContainer('Login information missing', 'You need to enter you login information first.')

    if Prefs['sync_watched'] is not True and Prefs['sync_ratings'] is not True:
        Log('You need to enable at least one type of actions to sync first.')
        return MessageContainer('No type selected', 'You need to enable at least one type of actions to sync first.')

    values = {
        'username': Prefs['username'],
        'password': Hash.SHA1(Prefs['password']),
        'extended': 'min'
    }

    movie_list = None
    show_list = None

    movies_rated_list = None
    episodes_rated_list = None

    # Get watched and rated lists from trakt
    if Prefs['sync_watched'] is True:
        movie_list = Trakt.request('user/library/movies/watched.json', values, param=Prefs['username'])
        show_list = Trakt.request('user/library/shows/watched.json', values, param=Prefs['username'])

    if Prefs['sync_ratings'] is True:
        movies_rated_list = Trakt.request('user/ratings/movies.json', values, param=Prefs['username'])
        episodes_rated_list = Trakt.request('user/ratings/episodes.json', values, param=Prefs['username'])

    # Go through the Plex library and update flags
    for section_type, key, title in itersections():
        # Sync movies
        if section_type == 'movie':
            for video in PMS.get_section_videos(key):
                pull_movie(movie_list, movies_rated_list, video)

        # Sync TV Shows
        if section_type == 'show':
            for directory in PMS.get_section_directories(key):
                tvdb_id = TVSHOW1_REGEXP.search(PMS.get_metadata_guid(directory.get('ratingKey'))).group(1)

                if tvdb_id is not None:
                    pull_show(show_list, episodes_rated_list, directory, tvdb_id)

    Log('Syncing is done!')
    Dict['Last_sync_down'] = Datetime.Now()

    return MessageContainer('Done', 'Syncing is done!')

@route('/applications/trakttv/syncsection')
def SyncSection(key):
    if Prefs['username'] is None:
        Log('You need to enter you login information first.')

        return MessageContainer(
            'Login information missing',
            'You need to enter you login information first.'
        )

    prefs = (Prefs['sync_watched'], Prefs['sync_ratings'], Prefs['sync_collection'])
    if all(x for x in prefs if x is not True):
        Log('You need to enable at least one type of actions to sync first.')

        return MessageContainer(
            'No type selected',
            'You need to enable at least one type of actions to sync first.'
        )

    # Sync the library with trakt.tv
    all_movies = []
    all_episodes = []
    ratings_movies = []
    ratings_episodes = []
    collection_movies = []
    collection_episodes = []
    Log(key)

    for value in key.split(','):
        item_kind = PMS.get_section(value).xpath('//MediaContainer')[0].get('viewGroup')

        if item_kind == 'movie':
            for video in PMS.get_section_videos(value):
                pms_metadata = None
                if Prefs['sync_collection'] is True:
                    pms_metadata = PMS.metadata(video.get('ratingKey'))
                    collection_movie = pms_metadata
                    collection_movies.append(collection_movie)

                if video.get('viewCount') > 0:
                    Log('You have seen %s', video.get('title'))
                    if video.get('type') == 'movie':
                        if pms_metadata is None:
                            pms_metadata = PMS.metadata(video.get('ratingKey'))
                        movie_dict = pms_metadata
                        movie_dict['plays'] = int(video.get('viewCount'))
                        # Remove the duration value since we won't need that!
                        #movie_dict.pop('duration')
                        all_movies.append(movie_dict)
                    else:
                        Log('Unknown item %s' % video.get('ratingKey'))
                if video.get('userRating') is not None:
                    if pms_metadata is None:
                        pms_metadata = PMS.metadata(video.get('ratingKey'))
                    rating_movie = pms_metadata
                    rating_movie['rating'] = int(video.get('userRating'))
                    ratings_movies.append(rating_movie)
        elif item_kind == 'show':
            for directory in PMS.get_section_directories(value):
                try:
                    tvdb_id = TVSHOW1_REGEXP.search(PMS.get_metadata_guid(directory.get('ratingKey'))).group(1)
                except:
                    tvdb_id = None

                tv_show = {
                    'title': directory.get('title')
                }
                if directory.get('year') is not None:
                    tv_show['year'] = int(directory.get('year'))
                if tvdb_id is not None:
                    tv_show['tvdb_id'] = tvdb_id

                seen_episodes = []
                collected_episodes = []

                episodes = PMS.get_metadata_leaves(directory.get('ratingKey')).xpath('//Video')

                for episode in episodes:
                    try:
                        collected_episode = {
                            'season': int(episode.get('parentIndex')),
                            'episode': int(episode.get('index'))
                        }
                        collected_episodes.append(collected_episode)
                    except: pass
                    if episode.get('viewCount') > 0:
                        try:
                            tv_episode = {
                                'season': int(episode.get('parentIndex')),
                                'episode': int(episode.get('index'))
                            }
                            seen_episodes.append(tv_episode)
                        except:
                            pass
                    if episode.get('userRating') is not None:
                        try:
                            rating_episode = {
                                'season': int(episode.get('parentIndex')),
                                'episode': int(episode.get('index')),
                                'rating': int(episode.get('userRating')),
                                'title': directory.get('title')
                            }
                            if directory.get('year') is not None:
                                rating_episode['year'] = int(directory.get('year'))
                            if tvdb_id is not None:
                                rating_episode['tvdb_id'] = tvdb_id
                            ratings_episodes.append(rating_episode)
                        except:
                            pass
                if len(seen_episodes) > 0:
                    seen_tv_show = {
                        'title': directory.get('title')
                    }
                    if directory.get('year') is not None:
                        seen_tv_show['year'] = int(directory.get('year'))
                    if tvdb_id is not None:
                        seen_tv_show['tvdb_id'] = tvdb_id
                    seen_tv_show['episodes'] = seen_episodes
                    all_episodes.append(seen_tv_show)
                tv_show['episodes'] = collected_episodes
                collection_episodes.append(tv_show)

    Log('Found %s movies' % len(all_movies))
    Log('Found %s series' % len(all_episodes))

    if Prefs['sync_ratings'] is True:
        if len(ratings_episodes) > 0:
            values = {
                'username': Prefs['username'],
                'password': Hash.SHA1(Prefs['password']),
                'episodes': ratings_episodes
            }
            status = Trakt.request('rate/episodes', values)
            Log("Trakt responded with: %s " % status)

        if len(ratings_movies) > 0:
            values = {
                'username': Prefs['username'],
                'password': Hash.SHA1(Prefs['password']),
                'movies': ratings_movies
            }
            status = Trakt.request('rate/movies', values)
            Log("Trakt responded with: %s " % status)

    if Prefs['sync_watched'] is True:
        if len(all_movies) > 0:
            values = {
                'username': Prefs['username'],
                'password': Hash.SHA1(Prefs['password']),
                'movies': all_movies
            }
            status = Trakt.request('movie/seen', values)
            Log("Trakt responded with: %s " % status)

        for episode in all_episodes:
            episode['username'] = Prefs['username']
            episode['password'] = Hash.SHA1(Prefs['password'])
            status = Trakt.request('show/episode/seen', episode)
            Log("Trakt responded with: %s " % status)

    if Prefs['sync_collection'] is True:
        if len(collection_movies) > 0:
            values = {
                'username': Prefs['username'],
                'password': Hash.SHA1(Prefs['password']),
                'movies': collection_movies
            }
            status = Trakt.request('movie/library', values)
            Log("Trakt responded with: %s " % status)

        for episode in collection_episodes:
            episode['username'] = Prefs['username']
            episode['password'] = Hash.SHA1(Prefs['password'])
            status = Trakt.request('show/episode/library', episode)
            Log("Trakt responded with: %s " % status)

    Log('Syncing is done!')
    Dict['Last_sync_up'] = Datetime.Now()
    return MessageContainer('Done', 'Syncing is done!')
