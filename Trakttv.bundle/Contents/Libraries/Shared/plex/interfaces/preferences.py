from plex.interfaces.core.base import Interface


class PreferencesInterface(Interface):
    path = ':/prefs'

    def get(self, id=None):
        response = self.http.get()

        container = self.parse(response, {
            'MediaContainer': ('MediaContainer', {
                'Setting': 'Setting'
            })
        })

        if id is None:
            return container

        for setting in container:
            if setting.id == id:
                return setting

        return None

    def set(self, id, value):
        self.http.put(query={
            id: self.to_setting_value(value, type(value))
        })

    def to_setting_value(self, value, value_type=None):
        if value is None:
            return None

        if value_type is bool:
            return str(value).lower()

        return str(value)
