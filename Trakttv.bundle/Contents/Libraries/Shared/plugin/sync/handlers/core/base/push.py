class PushHandler(object):
    @staticmethod
    def build_action(action, p_guid, p_item, p_value, **kwargs):
        data = {}

        if action in ['added', 'changed']:
            data['p_guid'] = p_guid
            data['p_item'] = p_item

            data['p_value'] = p_value

        data.update(kwargs)
        return data

    def get_action(self, p_value, t_value):
        if p_value is None and t_value is not None:
            return 'removed'

        if p_value is not None and t_value is None:
            return 'added'

        if p_value != t_value:
            return 'changed'

        return None
