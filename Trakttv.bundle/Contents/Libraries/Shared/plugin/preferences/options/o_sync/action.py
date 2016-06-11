from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.core.description import Description
from plugin.preferences.options.o_sync.constants import ACTION_MODE_LABELS_BY_KEY
from plugin.sync.core.enums import SyncActionMode


class SyncActionOption(SimpleOption):
    key = 'sync.action.mode'
    type = 'enum'

    choices = ACTION_MODE_LABELS_BY_KEY
    default = None
    scope = 'server'

    group = (_('Advanced'), _('Sync'))
    label = _('Action')
    description = Description(
        _("Action to perform during syncs."), [
            (_("Update"), _(
                "Update Trakt.tv and Plex with any changes"
            )),
            (_("Log"), _(
                "Don't perform any updates, just display changes in the plugin log file"
            ))
        ]
    )
    order = 120

    @property
    def value(self):
        value = super(SyncActionOption, self).value

        if value is None:
            return SyncActionMode.Update

        return value

