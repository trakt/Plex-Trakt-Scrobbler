from trakt.interfaces.base import Interface
from trakt.mapper.summary import SummaryMapper


class ShowsInterface(Interface):
    path = 'shows'

    def get(self, id):
        response = self.http.get(
            str(id)
        )

        return SummaryMapper.show(
            self.get_data(response)
        )

    def seasons(self, id):
        response = self.http.get(str(id), [
            'seasons'
        ])

        return SummaryMapper.seasons(
            self.get_data(response)
        )

    def season(self, id, season):
        response = self.http.get(str(id), [
            'seasons', str(season)
        ])

        return SummaryMapper.episodes(
            self.get_data(response)
        )

    def episode(self, id, season, episode):
        response = self.http.get(str(id), [
            'seasons', str(season),
            'episodes', str(episode)
        ])

        return SummaryMapper.episode(
            self.get_data(response)
        )
