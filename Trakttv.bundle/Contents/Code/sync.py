from pms import PMS_URL, TVSHOW1_REGEXP, get_metadata_from_pms
from helpers import SyncDownString, SyncUpString
from trakt import Trakt

@route('/applications/trakttv/manuallysync')
def ManuallySync():

    if Prefs['username'] is None:
        return MessageContainer("Error", "No login information entered.")

    oc = ObjectContainer(title2=L("Sync"))

    all_keys = []

    try:
        sections = XML.ElementFromURL(PMS_URL % 'sections', errors='ignore').xpath('//Directory')
        for section in sections:
            key = section.get('key')
            title = section.get('title')
            #Log('%s: %s' %(title, key))
            if section.get('type') == 'show' or section.get('type') == 'movie':
                oc.add(DirectoryObject(
                    key=Callback(SyncSection, key=[key]),
                    title='Sync items in "' + title + '" to Trakt.tv',
                    summary='Sync your ' + SyncUpString() + ' in the "' + title +
                            '" section of your Plex library with your Trakt.tv account.',
                    thumb=R("icon-sync_up.png")
                ))
                all_keys.append(key)
    except:
        Log('Failed to load sections from PMS')
        pass

    if len(all_keys) > 1:
        oc.add(DirectoryObject(
            key=Callback(SyncSection, key=",".join(all_keys)),
            title='Sync items in ALL sections to Trakt.tv',
            summary='Sync your ' + SyncUpString() +
                    ' in all sections of your Plex library with your Trakt.tv account.',
            thumb=R("icon-sync_up.png")))

    oc.add(DirectoryObject(
        key=Callback(ManuallyTrakt),
        title='Sync items from Trakt.tv',
        summary='Sync your ' + SyncDownString() + ' items on Trakt.tv with your Plex library.',
        thumb=R("icon-sync_down.png")
    ))

    return oc

@route('/applications/trakttv/syncplex')
def SyncPlex():
    #LAST_SYNC_UP = Dict['Last_sync_up']
    try:
        if (Dict['Last_sync_up'] + Datetime.Delta(minutes=360)) > Datetime.Now():
            Log('Not enough time since last sync, breaking!')
        else:
            all_keys = []
            try:
                sections = XML.ElementFromURL(PMS_URL % 'sections', errors='ignore').xpath('//Directory')
                for section in sections:
                    if section.get('type') == 'show' or section.get('type') == 'movie':
                        all_keys.append(key)
            except:
                Log("Couldn't find PMS instance")

            for key in all_keys:
                try:
                    SyncSection(key)
                except:
                    pass
    except:
        all_keys = []
        try:
            sections = XML.ElementFromURL(PMS_URL % 'sections', errors='ignore').xpath('//Directory')
            for section in sections:
                if section.get('type') == 'show' or section.get('type') == 'movie':
                    all_keys.append(key)
        except:
            Log("Couldn't find PMS instance")

        for key in all_keys:
            try:
                SyncSection(key)
            except: pass

@route('/applications/trakttv/synctrakt')
def SyncTrakt():
    LAST_SYNC_DOWN = Dict['Last_sync_down']
    try:
        if (LAST_SYNC_DOWN + Datetime.Delta(minutes=360)) > Datetime.Now():
            Log('Not enough time since last sync, breaking!')
        else:
            ManuallyTrakt()
    except:
        ManuallyTrakt()

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

    try:
        if Prefs['sync_watched'] is True:
            # Get data from Trakt.tv
            movie_list = Trakt.request('user/library/movies/watched.json', values, param = Prefs['username'])
            show_list = Trakt.request('user/library/shows/watched.json', values, param = Prefs['username'])

        if Prefs['sync_ratings'] is True:
            # Get data from Trakt.tv
            movies_rated_list = Trakt.request('user/ratings/movies.json', values, param=Prefs['username'])
            episodes_rated_list = Trakt.request('user/ratings/episodes.json', values, param=Prefs['username'])
    except:
        return MessageContainer(
            'Failed to load data from Trakt',
            'Something went wrong while getting data from Trakt. Please check the log for details.'
        )

    # Go through the Plex library and update flags
    library_sections = XML.ElementFromURL(PMS_URL % 'sections', errors='ignore').xpath('//Directory')
    for library_section in library_sections:
        if library_section.get('type') == 'movie':
            videos = XML.ElementFromURL(
                PMS_URL % ('sections/%s/all' % library_section.get('key')), errors='ignore'
            ).xpath('//Video')

            for video in videos:
                metadata = get_metadata_from_pms(video.get('ratingKey'))
                if 'imdb_id' in metadata:
                    if Prefs['sync_watched'] is True:
                        for movie in movie_list:
                            if 'imdb_id' in movie:
                                if metadata['imdb_id'] == movie['imdb_id']:
                                    Log('Found %s with id %s' % (metadata['title'], video.get('ratingKey')))
                                    # TODO: Dont mark a movie as seen if it allready is seen. Messes up the library.
                                    if video.get('viewCount') > 0:
                                        Log('The movie %s is already marked as seen in the library.' % metadata['title'])
                                    else:
                                        HTTP.Request('http://localhost:32400/:/scrobble?identifier=com.plexapp.plugins.library&key=%s' % video.get('ratingKey'))
                    if Prefs['sync_ratings'] is True:
                        for movie in movies_rated_list:
                            if 'imdb_id' in movie:
                                if metadata['imdb_id'] == movie['imdb_id']:
                                    Log('Found %s with id %s' % (metadata['title'], video.get('ratingKey')))
                                    HTTP.Request('http://localhost:32400/:/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (video.get('ratingKey'), movie['rating_advanced']))
        elif library_section.get('type') == 'show':
            directories = XML.ElementFromURL(PMS_URL % ('sections/%s/all' % library_section.get('key')), errors='ignore').xpath('//Directory')
            for directory in directories:
                try:
                    tvdb_id = TVSHOW1_REGEXP.search(XML.ElementFromURL(
                        PMS_URL % ('metadata/%s' % directory.get('ratingKey')), errors='ignore'
                    ).xpath('//Directory')[0].get('guid')).group(1)

                    if tvdb_id is not None:
                        if Prefs['sync_watched'] is True:
                            for show in show_list:
                                if tvdb_id == show['tvdb_id']:
                                    Log('We have a match for %s' % show['title'])

                                    episodes = XML.ElementFromURL(
                                        PMS_URL % ('metadata/%s/allLeaves' % directory.get('ratingKey')), errors='ignore'
                                    ).xpath('//Video')

                                    for episode in episodes:
                                        for season in show['seasons']:
                                            if int(season['season']) == int(episode.get('parentIndex')):
                                                if int(episode.get('index')) in season['episodes']:
                                                    Log('Marking %s episode %s with key: %s as seen.' % (episode.get('grandparentTitle'), episode.get('title'), episode.get('ratingKey')))
                                                    if episode.get('viewCount') > 0:
                                                        Log('The episode %s is already marked as seen in the library.' % episode.get('title') )
                                                    else:
                                                        HTTP.Request('http://localhost:32400/:/scrobble?identifier=com.plexapp.plugins.library&key=%s' % episode.get('ratingKey'))
                        if Prefs['sync_ratings'] is True:
                            for show in episodes_rated_list:
                                if int(tvdb_id) == int(show['show']['tvdb_id']):
                                    episodes = XML.ElementFromURL(PMS_URL % ('metadata/%s/allLeaves' % directory.get('ratingKey')), errors='ignore').xpath('//Video')
                                    for episode in episodes:
                                        if int(show['episode']['season']) == int(episode.get('parentIndex')) and int(show['episode']['number']) == int(episode.get('index')):
                                            HTTP.Request('http://localhost:32400/:/rate?key=%s&identifier=com.plexapp.plugins.library&rating=%s' % (episode.get('ratingKey'), show['rating_advanced']))
                except: pass
    Log('Syncing is done!')
    Dict['Last_sync_down'] = Datetime.Now()
    return MessageContainer('Done', 'Syncing is done!')

@route('/applications/trakttv/syncsection')
def SyncSection(key):

    if Prefs['username'] is None:
        Log('You need to enter you login information first.')
        return MessageContainer('Login information missing', 'You need to enter you login information first.')

    if Prefs['sync_watched'] is not True and Prefs['sync_ratings'] is not True and Prefs['sync_collection'] is not True:
        Log('You need to enable at least one type of actions to sync first.')
        return MessageContainer('No type selected', 'You need to enable at least one type of actions to sync first.')

    # Sync the library with trakt.tv
    all_movies = []
    all_episodes = []
    ratings_movies = []
    ratings_episodes = []
    collection_movies = []
    collection_episodes = []
    Log(key)

    for value in key.split(','):
        item_kind = XML.ElementFromURL(
            PMS_URL % ('sections/%s/all' % value), errors='ignore'
        ).xpath('//MediaContainer')[0].get('viewGroup')

        if item_kind == 'movie':
            videos = XML.ElementFromURL(
                PMS_URL % ('sections/%s/all' % value), errors='ignore'
            ).xpath('//Video')

            for video in videos:
                pms_metadata = None
                if Prefs['sync_collection'] is True:
                    pms_metadata = get_metadata_from_pms(video.get('ratingKey'))
                    collection_movie = pms_metadata
                    collection_movies.append(collection_movie)

                if video.get('viewCount') > 0:
                    Log('You have seen %s', video.get('title'))
                    if video.get('type') == 'movie':
                        if pms_metadata is None:
                            pms_metadata = get_metadata_from_pms(video.get('ratingKey'))
                        movie_dict = pms_metadata
                        movie_dict['plays'] = int(video.get('viewCount'))
                        # Remove the duration value since we won't need that!
                        #movie_dict.pop('duration')
                        all_movies.append(movie_dict)
                    else:
                        Log('Unknown item %s' % video.get('ratingKey'))
                if video.get('userRating') is not None:
                    if pms_metadata is None:
                        pms_metadata = get_metadata_from_pms(video.get('ratingKey'))
                    rating_movie = pms_metadata
                    rating_movie['rating'] = int(video.get('userRating'))
                    ratings_movies.append(rating_movie)
        elif item_kind == 'show':
            directories = XML.ElementFromURL(
                PMS_URL % ('sections/%s/all' % value), errors='ignore'
            ).xpath('//Directory')

            for directory in directories:
                try:
                    tvdb_id = TVSHOW1_REGEXP.search(XML.ElementFromURL(
                        PMS_URL % ('metadata/%s' % directory.get('ratingKey')), errors='ignore'
                    ).xpath('//Directory')[0].get('guid')).group(1)
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

                episodes = XML.ElementFromURL(
                    PMS_URL % ('metadata/%s/allLeaves' % directory.get('ratingKey')), errors='ignore'
                ).xpath('//Video')

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
