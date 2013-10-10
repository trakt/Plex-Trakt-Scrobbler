from pms import TVSHOW1_REGEXP, PMS
from helpers import SyncDownString, SyncUpString, finditems, iterget, extend, matches, all
from trakt import Trakt


def parse_section(section):
    return (
        section.get('type', None),
        section.get('key', None),
        section.get('title', None)
    )


def itersections(types=('show', 'movie')):
    """Iterate over valid PMS sections of type 'show' or 'movie'"""
    result = []

    for section in [parse_section(s) for s in PMS.get_sections()]:
        # Ensure fields exist
        if all(v is not None for v in section):
            section_type, key, title = section
            # Ensure section is of type 'show' or 'movie'
            if section_type in types:
                result.append((section_type, key, title))

    return result


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

    if LAST_SYNC_DOWN and (LAST_SYNC_DOWN + Datetime.Delta(minutes=360)) > Datetime.Now():
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
                            episode.get('grandparentTitle'), episode.get('title'), episode.get('ratingKey')
                        ))

                        if not PMS.scrobble(episode):
                            Log('The episode %s is already marked as seen in the library.' % episode.get('title'))
    # Sync ratings
    if Prefs['sync_ratings'] is True:
        for show in [x for x in rated if x['show']['tvdb_id'] == tvdb_id]:
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

    values = {'extended': 'min'}

    movie_list = None
    show_list = None

    movies_rated_list = None
    episodes_rated_list = None

    # Get watched and rated lists from trakt
    if Prefs['sync_watched'] is True:
        movie_list = Trakt.request('user/library/movies/watched.json', values, param=Prefs['username']).get('result')
        show_list = Trakt.request('user/library/shows/watched.json', values, param=Prefs['username']).get('result')

    if Prefs['sync_ratings'] is True:
        movies_rated_list = Trakt.request('user/ratings/movies.json', values, param=Prefs['username']).get('result')
        episodes_rated_list = Trakt.request('user/ratings/episodes.json', values, param=Prefs['username']).get('result')

    if not all([movie_list, show_list, movies_rated_list, episodes_rated_list]):
        return MessageContainer('Network error', 'Network error while requesting current trakt data.')

    # Go through the Plex library and update flags
    for section_type, key, title in itersections():
        # Sync movies
        if section_type == 'movie':
            for video in PMS.get_section_videos(key):
                pull_movie(movie_list, movies_rated_list, video)

        # Sync TV Shows
        if section_type == 'show':
            for directory in PMS.get_section_directories(key):
                tvdb_id = TVSHOW1_REGEXP.search(PMS.get_metadata_guid(directory.get('ratingKey'))).group(2)

                if tvdb_id is not None:
                    pull_show(show_list, episodes_rated_list, directory, tvdb_id)

    Log('Syncing is done!')
    Dict['Last_sync_down'] = Datetime.Now()

    return MessageContainer('Done', 'Syncing is done!')


def push_movie(all_movies, collected, rated, video):
    pms_metadata = None

    if Prefs['sync_collection'] is True:
        pms_metadata = PMS.metadata(video.get('ratingKey'))
        collected.append(pms_metadata)

    if video.get('viewCount') > 0:
        Log('You have seen %s', video.get('title'))
        if video.get('type') == 'movie':
            if pms_metadata is None:
                pms_metadata = PMS.metadata(video.get('ratingKey'))

            movie_dict = pms_metadata
            #movie_dict['plays'] = int(video.get('viewCount'))
            #movie_dict.pop('duration')

            all_movies.append(movie_dict)
        else:
            Log('Unknown item %s' % video.get('ratingKey'))

    if video.get('userRating') is not None:
        if pms_metadata is None:
            pms_metadata = PMS.metadata(video.get('ratingKey'))

        rating_movie = pms_metadata
        rating_movie['rating'] = int(video.get('userRating'))

        rated.append(rating_movie)


def push_show(all_episodes, collected, rated, directory):
    tvdb_id = TVSHOW1_REGEXP.search(PMS.get_metadata_guid(directory.get('ratingKey'))).group(2)

    tv_show = {
        'title': directory.get('title')
    }

    year = directory.get('year', None)
    if year is not None:
        tv_show['year'] = int(year)

    if tvdb_id is not None:
        tv_show['tvdb_id'] = tvdb_id

    seen_episodes = []
    collected_episodes = []

    episodes = PMS.get_metadata_leaves(directory.get('ratingKey')).xpath('//Video')

    for episode, parentIndex, index in iterget(episodes, ['parentIndex', 'index']):
        season_num = int(parentIndex)
        episode_num = int(index)

        base_episode = {
            'season': season_num,
            'episode': episode_num
        }

        collected_episodes.append(base_episode)

        if episode.get('viewCount') > 0:
            seen_episodes.append(extend(base_episode))

        if episode.get('userRating') is not None:
            rating_episode = extend(base_episode, {
                'title': directory.get('title'),
                'rating': int(episode.get('userRating'))
            })

            if year is not None:
                rating_episode['year'] = year

            if tvdb_id is not None:
                rating_episode['tvdb_id'] = tvdb_id

            rated.append(rating_episode)

    if len(seen_episodes) > 0:
        seen_tv_show = {
            'title': directory.get('title')
        }

        if year is not None:
            seen_tv_show['year'] = year

        if tvdb_id is not None:
            seen_tv_show['tvdb_id'] = tvdb_id

        seen_tv_show['episodes'] = seen_episodes
        all_episodes.append(seen_tv_show)

    tv_show['episodes'] = collected_episodes
    collected.append(tv_show)


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

        # Sync movies
        if item_kind == 'movie':
            for video in PMS.get_section_videos(value):
                push_movie(all_movies, collection_movies, ratings_movies, video)

        # Sync TV Shows
        if item_kind == 'show':
            for directory in PMS.get_section_directories(value):
                push_show(all_episodes, collection_episodes, ratings_episodes, directory)

    Log('Found %s movies' % len(all_movies))
    Log('Found %s series' % len(all_episodes))

    if Prefs['sync_ratings'] is True:
        if len(ratings_episodes) > 0:
            status = Trakt.request('rate/episodes', {
                'episodes': ratings_episodes
            })
            #Log("Trakt responded with: %s " % status)

        if len(ratings_movies) > 0:
            status = Trakt.request('rate/movies', {
                'movies': ratings_movies
            })
            #Log("Trakt responded with: %s " % status)

    if Prefs['sync_watched'] is True:
        if len(all_movies) > 0:
            status = Trakt.request('movie/seen', {
                'movies': all_movies
            })
            #Log("Trakt responded with: %s " % status)

        for episode in all_episodes:
            status = Trakt.request('show/episode/seen', episode)
            #Log("Trakt responded with: %s " % status)

    if Prefs['sync_collection'] is True:
        if len(collection_movies) > 0:
            status = Trakt.request('movie/library', {
                'movies': collection_movies
            })
            #Log("Trakt responded with: %s " % status)

        for episode in collection_episodes:
            status = Trakt.request('show/episode/library', episode)
            #Log("Trakt responded with: %s " % status)

    Log('Syncing is done!')
    Dict['Last_sync_up'] = Datetime.Now()
    return MessageContainer('Done', 'Syncing is done!')

@route('/applications/trakttv/collectionsync')
def CollectionSync(itemID,do):
    metadata = PMS.metadata(itemID)

    #cancel, if metadata is not there yet
    if not 'tvdb_id' in metadata and not 'imdb_id' in metadata and not 'tmdb_id' in metadata:
        return

    if do == 'add':
        do_action = 'library'
    elif do == 'delete':
        do_action = 'unlibrary'
    else:
        return

    action = None
    if metadata['type'] == 'episode':
        action = 'show/episode/%s' % do_action
    elif metadata['type'] == 'movie':
        action = 'movie/%s' % do_action

    # Setup Data to send to Trakt
    values = dict()

    if metadata['type'] == 'episode':
        if metadata['tvdb_id'] == False:
            Log.Info('Added episode has no tvdb_id')
            return

        values['tvdb_id'] = metadata['tvdb_id']
        values['title'] = metadata['title']
        if ('year' in metadata):
            values['year'] = metadata['year']
        values['episodes'] = [{'season' : metadata['season'],'episode' : metadata['episode']}]
    elif metadata['type'] == 'movie':
        if metadata['imdb_id'] == False and 'tmdb_id' in metadata and metadata['tmdb_id'] == False:
            Log.Info('Added movie has no imdb_id and no tmdb_id')
            return

        if (metadata['imdb_id'] != False):
            values['movies'] = [{'imdb_id' : metadata['imdb_id'],'title' : metadata['title'],'year' : metadata['year']}]
        elif (metadata['tmdb_id'] != False):
            values['movies'] = [{'tmdb_id' : metadata['tmdb_id'],'title' : metadata['title'],'year' : metadata['year']}]

    if action:
        Trakt.request(action, values)
