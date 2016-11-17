from plugin.models.core import db

from datetime import datetime, timedelta
from exception_wrappers.libraries.playhouse.apsw_ext import *
import logging
import requests

REFRESH_INTERVAL = timedelta(days=1)

log = logging.getLogger(__name__)


class Account(Model):
    class Meta:
        database = db

    name = CharField(null=True, unique=True)
    thumb = TextField(null=True)

    deleted = BooleanField(default=False)
    refreshed_at = DateTimeField(null=True)

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

    @property
    def refreshed_ts(self):
        if self.refreshed_at is None:
            return None

        return (self.refreshed_at - datetime(1970, 1, 1)).total_seconds()

    def thumb_url(self, update=False):
        if self.deleted or (self.thumb and not update):
            return self.thumb

        # Build thumb from `plex` and `trakt` accounts
        thumb = self.build_thumb()

        # If `thumb` has changed, store in database
        if thumb != self.thumb:
            self.thumb = thumb
            self.save()

        return thumb

    def refresh(self, force=False, save=True):
        if self.deleted:
            return False

        # Check if refresh is required
        if self.refresh_required():
            force = True

        # Only refresh account every `REFRESH_INTERVAL`
        if not force and self.refreshed_at:
            since_refresh = datetime.utcnow() - self.refreshed_at

            if since_refresh < REFRESH_INTERVAL:
                return False

        # Retrieve trakt/plex accounts
        p = self.plex
        t = self.trakt

        # Set `name` to trakt/plex username (if `name` isn't already set)
        if (self.name is None or self.name == 'administrator') and (t or p):
            self.name = t.username or p.username

        # Update account thumb
        self.thumb = self.build_thumb(
            plex=p,
            trakt=t
        )

        # Store changes in database
        self.refreshed_at = datetime.utcnow()

        if save:
            self.save()

        return True

    def refresh_required(self):
        if self.name is None:
            return True

        if self.thumb is None:
            return True

        return False

    def build_thumb(self, plex=None, trakt=None):
        if self.deleted:
            return None

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
            'name': self.name,
            'deleted': self.deleted,

            'thumb_url': self.thumb_url()
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
