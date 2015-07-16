from plugin.models.core import db

from playhouse.apsw_ext import *
import logging
import requests

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

    def refresh(self, save=True):
        # Retrieve trakt/plex accounts
        p = self.plex
        t = self.trakt

        # Set `name` to trakt username (if `name` isn't already set)
        if self.name is None:
            self.name = t.username

        # Update account thumb
        self.thumb = self.build_thumb(
            plex=p,
            trakt=t
        )

        # Store changes in database
        if save:
            self.save()

    def build_thumb(self, plex=None, trakt=None):
        # Check if trakt thumbnail exists
        t = trakt or self.trakt
        t_thumb = t.thumb_url('404') if t else None

        if t_thumb:
            response = requests.get(t_thumb)

            # Check response is valid
            if 200 <= response.status_code < 300:
                log.debug('Using trakt account thumbnail')
                return t.thumb_url()

        # Return plex thumbnail
        p = plex or self.plex
        p_thumb = p.thumb_url() if p else None

        return p_thumb

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
