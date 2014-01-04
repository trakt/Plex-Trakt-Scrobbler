from core.helpers import finditems, iterget, extend, matches, all, try_convert, itersections
from core.trakt import Trakt
from plex.media_server import PMS, TVSHOW1_REGEXP


@route('/applications/trakttv/syncplex')
def SyncPlex():
    if (Dict['Last_sync_up'] + Datetime.Delta(minutes=360)) > Datetime.Now():
        Log.Info('Not enough time since last sync, breaking!')
    else:
        for (_, key, _) in itersections(PMS.get_sections()):
            SyncSection(key)


@route('/applications/trakttv/synctrakt')
def SyncTrakt():
    LAST_SYNC_DOWN = Dict['Last_sync_down']

    if LAST_SYNC_DOWN and (LAST_SYNC_DOWN + Datetime.Delta(minutes=360)) > Datetime.Now():
        Log.Info('Not enough time since last sync, breaking!')
    else:
        ManuallyTrakt()


def pull_movie(watched, rated, video):
    # Pull metadata
    metadata = PMS.metadata(video.get('ratingKey'))
    if not metadata or 'imdb_id' not in metadata:
        Log.Warn('Invalid metadata for movie with key %s (network error or missing IMDB ID)' % video.get('ratingKey'))
        return

    # Sync watched
    if Prefs['sync_watched'] is True:
        for movie in finditems(metadata, watched, 'imdb_id'):
            Log.Debug('Found %s with id %s' % (metadata['title'], video.get('ratingKey')))

            if not PMS.scrobble(video):
                Log.Debug('The movie %s is already marked as seen in the library.' % metadata['title'])

    # Sync ratings
    if Prefs['sync_ratings'] is True:
        for movie in finditems(metadata, rated, 'imdb_id'):
            Log.Debug('Found %s with id %s' % (metadata['title'], video.get('ratingKey')))
            PMS.rate(video, movie['rating_advanced'])


def pull_show(watched, rated, directory, tvdb_id):
    # Sync watched
    if Prefs['sync_watched'] is True:
        for show in [x for x in watched if x['tvdb_id'] == tvdb_id]:
            Log.Debug('We have a match for %s' % show['title'])

            episodes = PMS.get_metadata_leaves(directory.get('ratingKey'))
            if not episodes:
                Log.Warn('Unable to fetch episodes for show with id %s' % directory.get('ratingKey'))
                continue

            for episode in episodes.xpath('//Video'):
                season_num = try_convert(episode.get('parentIndex'), int)
                episode_num = try_convert(episode.get('index'), int)

                # Skip episodes with missing season or episode numbers
                if season_num is None or episode_num is None:
                    continue

                for season in matches(season_num, show['seasons'], lambda x: int(x['season'])):

                    if episode_num in season['episodes']:
                        Log.Debug('Marking %s episode %s with key: %s as seen.' % (
                            episode.get('grandparentTitle'), episode.get('title'), episode.get('ratingKey')
                        ))

                        if not PMS.scrobble(episode):
                            Log.Debug('The episode %s is already marked as seen in the library.' % episode.get('title'))

    # Sync ratings
    if Prefs['sync_ratings'] is True:
        for show in [x for x in rated if x['show']['tvdb_id'] == tvdb_id]:
            show_season = try_convert(show['episode']['season'], int)
            show_episode = try_convert(show['episode']['number'], int)

            # Skip episodes with missing season or episode numbers
            if show_season is None or show_episode is None:
                continue

            episodes = PMS.get_metadata_leaves(directory.get('ratingKey'))
            if not episodes:
                Log.Warn('Unable to fetch episodes for show with id %s' % directory.get('ratingKey'))
                continue

            for episode in episodes.xpath('//Video'):
                if show_season == int(episode.get('parentIndex')) and show_episode == int(episode.get('index')):
                    PMS.rate(episode, show['rating_advanced'])


def match_tvdb_id(rating_key):
    if not rating_key:
        Log.Warn("Guid matching failed, key isn't a valid string")
        return None

    guid = PMS.get_metadata_guid(rating_key)

    match = TVSHOW1_REGEXP.search(guid)
    if not match:
        Log.Warn('Guid matching failed on "%s"' % guid)
        return None

    return match.group(2)


@route('/applications/trakttv/manuallytrakt')
def ManuallyTrakt():
    if Prefs['username'] is None:
        Log.Info('You need to enter you login information first.')
        return MessageContainer('Login information missing', 'You need to enter you login information first.')

    if Prefs['sync_watched'] is not True and Prefs['sync_ratings'] is not True:
        Log.Info('You need to enable at least one type of actions to sync first.')
        return MessageContainer('No type selected', 'You need to enable at least one type of actions to sync first.')

    values = {'extended': 'min'}

    movie_list = None
    show_list = None

    movies_rated_list = None
    episodes_rated_list = None

    # Get watched and rated lists from trakt
    if Prefs['sync_watched'] is True:
        movie_list = Trakt.request(
            'user/library/movies/watched.json',
            values,
            param=Prefs['username']
        ).get('data')

        show_list = Trakt.request(
            'user/library/shows/watched.json',
            values,
            param=Prefs['username']
        ).get('data')

        if not all([x is not None for x in [movie_list, show_list]]):
            return MessageContainer('Network error', 'Network error while requesting watched items from trakt.')

    if Prefs['sync_ratings'] is True:
        movies_rated_list = Trakt.request(
            'user/ratings/movies.json',
            values,
            param=Prefs['username']
        ).get('data')

        episodes_rated_list = Trakt.request(
            'user/ratings/episodes.json',
            values,
            param=Prefs['username']
        ).get('data')

        if not all([x is not None for x in [movies_rated_list, episodes_rated_list]]):
            return MessageContainer('Network error', 'Network error while requesting rated items from trakt.')

    # Go through the Plex library and update flags
    for section_type, key, title in itersections(PMS.get_sections()):
        # Sync movies
        if section_type == 'movie':
            for video in PMS.get_section_videos(key):
                pull_movie(movie_list, movies_rated_list, video)

        # Sync TV Shows
        if section_type == 'show':
            for directory in PMS.get_section_directories(key):
                tvdb_id = match_tvdb_id(directory.get('ratingKey'))
                if not tvdb_id:
                    continue

                if tvdb_id is not None:
                    pull_show(show_list, episodes_rated_list, directory, tvdb_id)

    Log.Info('Syncing is done!')
    Dict['Last_sync_down'] = Datetime.Now()

    return MessageContainer('Done', 'Syncing is done!')


def push_movie(all_movies, collected, rated, video):
    pms_metadata = None

    if Prefs['sync_collection'] is True:
        pms_metadata = PMS.metadata(video.get('ratingKey'))
        collected.append(pms_metadata)

    if video.get('viewCount') > 0:
        Log.Debug('You have seen %s', video.get('title'))
        if video.get('type') == 'movie':
            if pms_metadata is None:
                pms_metadata = PMS.metadata(video.get('ratingKey'))

            movie_dict = pms_metadata
            #movie_dict['plays'] = int(video.get('viewCount'))
            #movie_dict.pop('duration')

            all_movies.append(movie_dict)
        else:
            Log.Info('Unknown item %s' % video.get('ratingKey'))

    if video.get('userRating') is not None:
        if pms_metadata is None:
            pms_metadata = PMS.metadata(video.get('ratingKey'))

        rating_movie = pms_metadata
        rating_movie['rating'] = int(video.get('userRating'))

        rated.append(rating_movie)


def push_show(all_episodes, collected, rated, directory):
    tvdb_id = match_tvdb_id(directory.get('ratingKey'))
    if not tvdb_id:
        return

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

    episodes = PMS.get_metadata_leaves(directory.get('ratingKey'))
    if not episodes:
        Log.Warn('Unable to fetch episodes for show with id %s' % directory.get('ratingKey'))
        return

    for episode, parentIndex, index in iterget(episodes.xpath('//Video'), ['parentIndex', 'index']):
        # Ensure we have valid data
        if parentIndex is None or index is None:
            Log.Warn('Episode missing required data, skipping (key: %s)' % episode.get('ratingKey'))
            continue

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
        Log.Info('You need to enter you login information first.')

        return MessageContainer(
            'Login information missing',
            'You need to enter you login information first.'
        )

    prefs = (Prefs['sync_watched'], Prefs['sync_ratings'], Prefs['sync_collection'])
    if all(x is not True for x in prefs):
        Log.Info('You need to enable at least one type of actions to sync first.')

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

    for value in key.split(','):
        section = PMS.get_section(value)
        if not section:
            Log.Warn('Unable to get section with key "%s"' % value)
            continue

        item_kind = section.xpath('//MediaContainer')[0].get('viewGroup')

        # Sync movies
        if item_kind == 'movie':
            for video in PMS.get_section_videos(value):
                push_movie(all_movies, collection_movies, ratings_movies, video)

        # Sync TV Shows
        if item_kind == 'show':
            for directory in PMS.get_section_directories(value):
                push_show(all_episodes, collection_episodes, ratings_episodes, directory)

    Log.Info('Found %s movies' % len(all_movies))
    Log.Info('Found %s series' % len(all_episodes))

    if Prefs['sync_ratings'] is True:
        if len(ratings_episodes) > 0:
            Trakt.request('rate/episodes', {
                'episodes': ratings_episodes
            }, authenticate=True)

        if len(ratings_movies) > 0:
            Trakt.request('rate/movies', {
                'movies': ratings_movies
            }, authenticate=True)

    if Prefs['sync_watched'] is True:
        if len(all_movies) > 0:
            Trakt.request('movie/seen', {
                'movies': all_movies
            }, authenticate=True)

        for episode in all_episodes:
            Trakt.request('show/episode/seen', episode, authenticate=True)

    if Prefs['sync_collection'] is True:
        if len(collection_movies) > 0:
            Trakt.request('movie/library', {
                'movies': collection_movies
            }, authenticate=True)

        for episode in collection_episodes:
            Trakt.request('show/episode/library', episode, authenticate=True)

    Log.Info('Syncing is done!')
    Dict['Last_sync_up'] = Datetime.Now()
    return MessageContainer('Done', 'Syncing is done!')


@route('/applications/trakttv/collectionsync')
def CollectionSync(itemID, do):
    metadata = PMS.metadata(itemID)
    if not metadata:
        Log.Warn('Unable to fetch metadata for media with id %s' % itemID)
        return

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
    values = {}

    if metadata['type'] == 'episode':
        if not metadata.get('tvdb_id'):
            Log.Info('Added episode has no tvdb_id')
            return

        values['tvdb_id'] = metadata['tvdb_id']
        values['title'] = metadata['title']

        if 'year' in metadata:
            values['year'] = metadata['year']

        values['episodes'] = [{'season': metadata['season'], 'episode': metadata['episode']}]

    elif metadata['type'] == 'movie':
        if not metadata.get('imdb_id') and not metadata.get('tmdb_id'):
            Log.Info('Added movie has no imdb_id and no tmdb_id')
            return

        movie = {'title': metadata['title'], 'year': metadata['year']}

        if metadata['imdb_id']:
            movie['imdb_id'] = metadata['imdb_id']
        elif metadata['tmdb_id']:
            movie['tmdb_id'] = metadata['tmdb_id']

        values['movies'] = [movie]

    if action:
        Trakt.request(action, values, authenticate=True)
