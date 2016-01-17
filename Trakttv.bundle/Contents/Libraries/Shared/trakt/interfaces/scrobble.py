from trakt.interfaces.base import Interface, authenticated, application


class ScrobbleInterface(Interface):
    path = 'scrobble'

    @application
    @authenticated
    def action(self, action, movie=None, show=None, episode=None, progress=0, **kwargs):
        if movie and (show or episode):
            raise ValueError('Only one media type should be provided')

        if not movie and not episode:
            raise ValueError('Missing media item')

        data = {
            'progress': progress,
            'app_version': kwargs.get('app_version', '1.0'),
            'app_date': kwargs.get('app_date', '2014-08-29')
        }

        if movie:
            # TODO validate
            data['movie'] = movie
        elif episode:
            if show:
                data['show'] = show

            # TODO validate
            data['episode'] = episode

        response = self.http.post(
            action,
            data=data,

            authenticated=kwargs.get('authenticated', None)
        )

        return self.get_data(response)

    @application
    @authenticated
    def start(self, movie=None, show=None, episode=None, progress=0, **kwargs):
        return self.action(
            'start',
            movie, show, episode,
            progress,

            **kwargs
        )

    @application
    @authenticated
    def pause(self, movie=None, show=None, episode=None, progress=0, **kwargs):
        return self.action(
            'pause',
            movie, show, episode,
            progress,

            **kwargs
        )

    @application
    @authenticated
    def stop(self, movie=None, show=None, episode=None, progress=0, **kwargs):
        return self.action(
            'stop',
            movie, show, episode,
            progress,

            **kwargs
        )
