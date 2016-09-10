from CodernityDB.hash_index import HashIndex


class MultiIndex(HashIndex):

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(MultiIndex, self).__init__(*args, **kwargs)

    def insert(self, doc_id, key, start, size, status='o'):
        if isinstance(key, (list, tuple)):
            key = set(key)
        elif not isinstance(key, set):
            key = set([key])
        ins = super(MultiIndex, self).insert
        for curr_key in key:
            ins(doc_id, curr_key, start, size, status)
        return True

    def update(self, doc_id, key, u_start, u_size, u_status='o'):
        if isinstance(key, (list, tuple)):
            key = set(key)
        elif not isinstance(key, set):
            key = set([key])
        upd = super(MultiIndex, self).update
        for curr_key in key:
            upd(doc_id, curr_key, u_start, u_size, u_status)

    def delete(self, doc_id, key, start=0, size=0):
        if isinstance(key, (list, tuple)):
            key = set(key)
        elif not isinstance(key, set):
            key = set([key])
        delete = super(MultiIndex, self).delete
        for curr_key in key:
            delete(doc_id, curr_key, start, size)

    def get(self, key):
        return super(MultiIndex, self).get(key)

    def make_key_value(self, data):
        return data['l'], None


if __name__ == '__main__':
    from CodernityDB.database import Database
    db = Database('/tmp/db_test')
    db.create()
    db.add_index(MultiIndex(db.path, 'multi'))
    for x in xrange(2):
        d = dict(l=range(10 * x, 10 * (x + 1)))
        db.insert(d)
    for curr in db.all('multi'):
        print curr

    for curr in db.all('id'):
        nl = map(lambda x: x * 10, curr['l'])
        curr['l'] = nl
        db.update(curr)

    for curr in db.all('multi'):
        print curr

    for curr in db.all('id'):
        nl = map(lambda x: x % 3, curr['l'])
        curr['l'] = nl
        print nl
        db.update(curr)

    for curr in db.all('multi'):
        print curr

    for curr in db.get_many('multi', key=1, limit=-1):
        print curr
