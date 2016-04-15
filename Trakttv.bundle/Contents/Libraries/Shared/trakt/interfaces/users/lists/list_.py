from trakt.core.helpers import clean_username
from trakt.interfaces.base import Interface
from trakt.mapper import ListMapper, ListItemMapper


class UsersListInterface(Interface):
    path = 'users/*/lists/*'

    def get(self, username, id):
        # Send request
        response = self.http.get(
            '/users/%s/lists/%s' % (clean_username(username), id),
        )

        if response.status_code < 200 or response.status_code >= 300:
            return None

        # Parse response
        item = self.get_data(response)

        # Map item to list object
        return ListMapper.custom_list(
            self.client, item,
            username=username
        )

    def items(self, username, id, **kwargs):
        # Send request
        response = self.http.get(
            '/users/%s/lists/%s/items' % (clean_username(username), id),
        )

        if response.status_code < 200 or response.status_code >= 300:
            return None

        # Parse response
        items = self.get_data(response, **kwargs)

        if type(items) is not list:
            return None

        return [
            ListItemMapper.process(self.client, item, index=x + 1)
            for x, item in enumerate(items)
        ]

    #
    # Owner actions
    #

    def add(self, username, id, items, **kwargs):
        # Send request
        response = self.http.post(
            '/users/%s/lists/%s/items' % (clean_username(username), id),
            data=items
        )

        if response.status_code < 200 or response.status_code >= 300:
            return None

        # Parse response
        return self.get_data(response, **kwargs)

    def delete(self, username, id):
        # Send request
        response = self.http.delete(
            '/users/%s/lists/%s' % (clean_username(username), id)
        )

        return 200 <= response.status_code < 300

    def update(self, username, id, name=None, description=None, privacy=None, display_numbers=None,
               allow_comments=None, return_type='object', **kwargs):
        data = {
            'name': name,
            'description': description,

            'privacy': privacy,
            'allow_comments': allow_comments,
            'display_numbers': display_numbers
        }

        # Remove attributes with `None` values
        for key in list(data.keys()):
            if data[key] is not None:
                continue

            del data[key]

        # Send request
        response = self.http.put(
            '/users/%s/lists/%s' % (clean_username(username), id),
            data=data
        )

        if response.status_code < 200 or response.status_code >= 300:
            return None

        # Parse response
        item = self.get_data(response)

        if return_type == 'data':
            return item

        if return_type == 'object':
            # Map item to list object
            return ListMapper.custom_list(
                self.client, item,
                username=username
            )

        raise ValueError("Unsupported value for \"return_type\": %r", return_type)

    def remove(self, username, id, items, **kwargs):
        # Send request
        response = self.http.post(
            '/users/%s/lists/%s/items/remove' % (clean_username(username), id),
            data=items
        )

        if response.status_code < 200 or response.status_code >= 300:
            return None

        # Parse response
        return self.get_data(response, **kwargs)

    #
    # Actions
    #

    def like(self, username, id, **kwargs):
        # Send request
        response = self.http.post(
            '/users/%s/lists/%s/like' % (clean_username(username), id)
        )

        return 200 <= response.status_code < 300

    def unlike(self, username, id, **kwargs):
        # Send request
        response = self.http.delete(
            '/users/%s/lists/%s/like' % (clean_username(username), id)
        )

        return 200 <= response.status_code < 300
