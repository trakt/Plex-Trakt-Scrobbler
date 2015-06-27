from plugin.sync.handlers.core.base.media import MediaHandler


class PullHandler(MediaHandler):
    def get_action(self, p_value, t_value):
        if p_value is None and t_value is not None:
            return 'added'

        if p_value is not None and t_value is None:
            return 'removed'

        if p_value != t_value:
            return 'changed'

        return None

    #
    # Modes
    #

    def fast_pull(self, action, p_item, t_item, **kwargs):
        if not action:
            # No action provided
            return

        # Retrieve properties
        p_value, t_value = self.get_operands(p_item, t_item)

        # Execute action
        self.execute_action(
            action,

            p_item=p_item,
            p_value=p_value,
            t_value=t_value,
            **kwargs
        )

    def pull(self, p_item, t_item, **kwargs):
        # Retrieve properties
        p_value, t_value = self.get_operands(p_item, t_item)

        # Determine performed action
        action = self.get_action(p_value, t_value)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(
            action,

            p_item=p_item,
            p_value=p_value,
            t_value=t_value,
            **kwargs
        )
