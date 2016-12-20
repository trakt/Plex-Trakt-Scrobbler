from trakt.interfaces.base import Interface
from trakt.mapper.summary import SummaryMapper


class ShowsInterface(Interface):
    path = 'shows'

    def get(self, id, extended=None, **kwargs):
        response = self.http.get(str(id), query={
            'extended': extended
        })

        return SummaryMapper.show(
            self.client,
            self.get_data(response, **kwargs)
        )

    def trending(self, extended=None, **kwargs):
        response = self.http.get('trending', query={
            'extended': extended
        })

        return SummaryMapper.shows(
            self.client,
            self.get_data(response, **kwargs)
        )

    def next_episode(self, id, extended=None, **kwargs):
        response = self.http.get(str(id), 'next_episode', query={
            'extended': extended
        })

        return SummaryMapper.episode(
            self.client,
            self.get_data(response, **kwargs)
        )

    def last_episode(self, id, extended=None, **kwargs):
        response = self.http.get(str(id), 'last_episode', query={
            'extended': extended
        })

        return SummaryMapper.episode(
            self.client,
            self.get_data(response, **kwargs)
        )

    def seasons(self, id, extended=None, **kwargs):
        response = self.http.get(str(id), [
            'seasons'
        ], query={
            'extended': extended
        })

        return SummaryMapper.seasons(
            self.client,
            self.get_data(response, **kwargs)
        )

    def season(self, id, season, extended=None, **kwargs):
        response = self.http.get(str(id), [
            'seasons', str(season)
        ], query={
            'extended': extended
        })

        return SummaryMapper.episodes(
            self.client,
            self.get_data(response, **kwargs)
        )

    def episode(self, id, season, episode, extended=None, **kwargs):
        response = self.http.get(str(id), [
            'seasons', str(season),
            'episodes', str(episode)
        ], query={
            'extended': extended
        })

        return SummaryMapper.episode(
            self.client,
            self.get_data(response, **kwargs)
        )
