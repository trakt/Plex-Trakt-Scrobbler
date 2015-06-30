from plugin.models.core import db

from playhouse.apsw_ext import *
from urlparse import urlparse
import logging

log = logging.getLogger(__name__)


class Account(Model):
    class Meta:
        database = db

    name = CharField(null=True, unique=True)
    thumb = TextField(null=True)

    def __init__(self, *args, **kwargs):
        super(Account, self).__init__(*args, **kwargs)

        self._plex_account = None
        self._trakt_account = None

    @property
    def plex(self):
        if self._plex_account:
            return self._plex_account

        return self.plex_accounts.first()

    @plex.setter
    def plex(self, value):
        self._plex_account = value

    @property
    def trakt(self):
        if self._trakt_account:
            return self._trakt_account

        return self.trakt_accounts.first()

    @trakt.setter
    def trakt(self, value):
        self._trakt_account = value

    def thumb_url(self, update=False):
        if self.thumb and not update:
            return self.thumb

        # Build thumb from `plex` and `trakt` accounts
        thumb = self.build_thumb()

        # If `thumb` has changed, store in database
        if thumb != self.thumb:
            self.thumb = thumb
            self.save()

        return thumb

    def build_thumb(self):
        p = self.plex
        p_thumb = p.thumb_url() if p else None

        t = self.trakt
        t_thumb = t.thumb_url(p_thumb) if t else None

        if t_thumb:
            # Trakt gravatar (with built-in fallback to plex thumb)
            return t_thumb

        if p_thumb:
            # Plex gravatar
            return p_thumb

        if t and t.thumb:
            # Trakt raw
            return t.thumb

        if p:
            # Plex raw
            return p.thumb

        return None

    def to_json(self, full=False):
        result = {
            'id': self.id,
            'name': self.name
        }

        if not full:
            return result

        # plex
        plex = self.plex

        if plex:
            result['plex'] = plex.to_json(full=full)

        # trakt
        trakt = self.trakt

        if trakt:
            result['trakt'] = trakt.to_json(full=full)

        return result

    def __repr__(self):
        return '<Account name: %r>' % (
            self.name
        )
