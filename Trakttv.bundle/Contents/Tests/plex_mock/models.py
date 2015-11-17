class LibraryMetadata(object):
    def __init__(self, section=None):
        self.section = section


class LibrarySection(object):
    def __init__(self, title=None):
        self.title = title


class Session(object):
    def __init__(self, **kwargs):
        self.duration = None
        self.rating_key = None
        self.state = None
        self.view_offset = None

        self.update(**kwargs)

    @property
    def payload(self):
        return {
            'rating_key': self.rating_key,
            'view_offset': self.view_offset
        }

    def save(self):
        pass

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise KeyError('Unknown attribute with key %r', key)

            setattr(self, key, value)

    def __repr__(self):
        return '<Session state: %r>' % (
            self.state
        )
