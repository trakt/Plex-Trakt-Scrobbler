import core
import interface

from bootstrap import bootstrap
from interface.resources import Cover, Thumb

from plugin.core.constants import PLUGIN_NAME, PLUGIN_ART, PLUGIN_ICON, PLUGIN_IDENTIFIER


def Start():
    ObjectContainer.art = R(PLUGIN_ART)
    ObjectContainer.title1 = PLUGIN_NAME
    DirectoryObject.thumb = R(PLUGIN_ICON)
    DirectoryObject.art = R(PLUGIN_ART)
    PopupDirectoryObject.thumb = R(PLUGIN_ICON)
    PopupDirectoryObject.art = R(PLUGIN_ART)

    # Store current proxy details
    Dict['proxy_host'] = Prefs['proxy_host']

    Dict['proxy_username'] = Prefs['proxy_username']
    Dict['proxy_password'] = Prefs['proxy_password']

    # Store current language
    Dict['language'] = Prefs['language']

    # Start plugin bootstrap
    bootstrap.start()


@expose
def Api(*args, **kwargs):
    from plugin.api.core.manager import ApiManager

    import json

    try:
        data = ApiManager.process(
            Request.Method,
            Request.Headers,
            Request.Body,

            *args, **kwargs
        )

        return json.dumps(data)
    except Exception as ex:
        Log.Error('Unable to process API request (args: %r, kwargs: %r) - %s', args, kwargs, ex)
        return None


def ValidatePrefs():
    from core.helpers import spawn

    from plugin.core.environment import translate as _
    from plugin.models.account import Account
    from plugin.modules.migrations.account import AccountMigration
    from plugin.preferences import Preferences

    from plex import Plex
    import time

    # Retrieve plex token
    token_plex = AccountMigration.get_token(Request.Headers)

    # Retrieve current activity mode
    last_activity_mode = Preferences.get('activity.mode')

    if Request.Headers.get('X-Disable-Preference-Migration', '0') == '0':
        # Run account migration
        am = AccountMigration()
        am.run(token_plex)

        # Migrate server preferences
        Preferences.migrate()

        # Try migrate administrator preferences
        try:
            Preferences.initialize(account=1)
            Preferences.migrate(account=1)
        except Account.DoesNotExist:
            Log.Debug('Unable to migrate administrator preferences, no account found')
    else:
        Log.Debug('Ignoring preference migration (disabled by header)')

    # Restart if activity_mode has changed
    if RestartRequired(last_activity_mode):
        Log.Info('Restart required to apply changes, restarting plugin...')

        def restart():
            # Delay until after `ValidatePrefs` returns
            time.sleep(3)

            # Restart plugin
            Plex[':/plugins'].restart(PLUGIN_IDENTIFIER)

        spawn(restart, daemon=True)
        return MessageContainer(_("Success"), _("Success"))

    # Fire configuration changed callback
    spawn(bootstrap.on_configuration_changed, daemon=True)

    return MessageContainer(_("Success"), _("Success"))


def RestartRequired(last_activity_mode):
    from plugin.preferences import Preferences

    if Preferences.get('activity.mode') != last_activity_mode:
        return True

    for key in ['language', 'proxy_host', 'proxy_username', 'proxy_password']:
        if Prefs[key] != Dict[key]:
            return True

    return False
