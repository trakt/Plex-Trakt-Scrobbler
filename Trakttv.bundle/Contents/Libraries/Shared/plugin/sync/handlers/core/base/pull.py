class PullHandler(object):
    def get_action(self, p_value, t_value):
        if p_value is None and t_value is not None:
            return 'added'

        if p_value is not None and t_value is None:
            return 'removed'

        if p_value != t_value:
            return 'changed'

        return None
