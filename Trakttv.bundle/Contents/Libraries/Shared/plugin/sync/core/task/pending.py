class SyncPending(object):
    def __init__(self, task):
        self.task = task

        self._collections = {}

    def create(self, media, keys):
        if media == 'episodes':
            self._collections[media] = PendingEpisodesCollection(media, keys)
        else:
            self._collections[media] = PendingCollection(media, keys)

    def __getitem__(self, media):
        if media not in self._collections:
            raise ValueError('Collection %r hasn\'t been initialized' % (media,))

        return self._collections[media]


class PendingCollection(object):
    def __init__(self, media, keys):
        self.media = media
        self.keys = keys

    def remove(self, pk, *args):
        if pk not in self.keys:
            return False

        self.keys.remove(pk)
        return True


class PendingEpisodesCollection(PendingCollection):
    def remove(self, pk, identifier):
        if len(identifier) != 2:
            raise ValueError('Invalid value provided for the "identifier" parameter: %r' % (identifier,))

        if pk not in self.keys:
            return False

        if identifier not in self.keys[pk]:
            return False

        self.keys[pk].remove(identifier)
        return True
