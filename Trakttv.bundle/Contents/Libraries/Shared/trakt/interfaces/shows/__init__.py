from trakt.interfaces.base import Interface
from trakt.mapper.summary import SummaryMapper


class ShowsInterface(Interface):
    path = 'shows'

    def get(self, id, **kwargs):
        response = self.http.get(
            str(id)
        )

        return SummaryMapper.show(
            self.client,
            self.get_data(response, **kwargs)
        )

    def trending(self, **kwargs):
        response = self.http.get(
            'trending'
        )

        return SummaryMapper.shows(
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

    def season(self, id, season, **kwargs):
        response = self.http.get(str(id), [
            'seasons', str(season)
        ])

        return SummaryMapper.episodes(
            self.client,
            self.get_data(response, **kwargs)
        )

    def episode(self, id, season, episode, **kwargs):
        response = self.http.get(str(id), [
            'seasons', str(season),
            'episodes', str(episode)
        ])

        return SummaryMapper.episode(
            self.client,
            self.get_data(response, **kwargs)
        )
