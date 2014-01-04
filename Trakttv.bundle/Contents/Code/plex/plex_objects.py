class PlexMedia(object):
    def __init__(self, rating_key):
        self.rating_key = rating_key


class PlexShow(PlexMedia):
    def __init__(self, rating_key, sid):
        super(PlexShow, self).__init__(rating_key)

        self.sid = sid

    @classmethod
    def create(cls, directory, sid):
        return cls(directory.get('ratingKey'), sid)


class PlexMovie(PlexMedia):
    def __init__(self, rating_key):
        super(PlexMovie, self).__init__(rating_key)
