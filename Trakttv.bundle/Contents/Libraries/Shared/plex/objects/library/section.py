from plex.core.helpers import to_iterable
from plex.objects.container import Container
from plex.objects.core.base import Property
from plex.objects.directory import Directory


class Section(Directory):
    uuid = Property

    filters = Property(type=bool)
    refreshing = Property(type=bool)

    agent = Property
    scanner = Property
    language = Property

    created_at = Property('createdAt', int)

    def __transform__(self):
        self.path = '/library/sections/%s' % self.key

    def all(self):
        response = self.http.get('all')

        return self.parse(response, {
            'MediaContainer': ('MediaContainer', {
                'Directory': {
                    'artist':    'Artist',
                    'show':     'Show'
                },
                'Video': {
                    'movie':    'Movie'
                }
            })
        })


class SectionContainer(Container):
    filter_passes = lambda _, allowed, value: allowed is None or value in allowed

    def filter(self, titles=None, keys=None, types=None):
        titles = [x.lower() for x in to_iterable(titles)]
        keys = to_iterable(keys)
        types = to_iterable(types)

        for section in self:
            if not self.filter_passes(titles, section.title.lower()):
                continue

            if not self.filter_passes(keys, section.key):
                continue

            if not self.filter_passes(types, section.type):
                continue

            yield section
