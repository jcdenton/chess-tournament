# -*- encoding: utf-8 -*-
from random import shuffle, sample
import math

from models import Round, Game, Side


class SwissSystemTournament(object):
    __WIN_SCORE = 1.0
    __DRAW_SCORE = 0.5

    def get_round_count(self, tournament):
        return round(math.log(tournament.players.count(), 2)) + round(math.log(tournament.players.count(), 2))

    def finish_round(self):
        pass

    def add_next_round(self, tournament, name):
        # if self.get_round_count(tournament) <= tournament.round_set.count():
        #     raise IndexError()
        past_games = tournament.get_games()
        players = self.sort_players(tournament.players[:], past_games)
        r = tournament.round_set.create(name=name, tournament=tournament)
        games = [Game(round=r, **self.define_colors(pair)) for pair in self.make_pairs(players)]
        r.game_set.add(games)

    def make_pairs(self, players):
        pairs = self.pair_group(players)

        players_count = len(players)
        if players_count % 2 != 0:
            pairs.append(players[players_count - 1], None)

        return pairs

    def pair_group(self, players_group):
        players_count = len(players_group)
        return [(players_group[i], players_group[players_count / 2 + i]) for i in range(players_count / 2)]

    def define_colors(self, pair):
        return dict(zip(
            (Side.WHITE, Side.BLACK),
            sample(pair, 2)
        ))

    def sort_players(self, players, games):
        '''
        Sorts the players by their rating in the first round and by current tournament score in all the following ones.
        '''
        if len(games) == 0:
            players = self.sort_by_rating(players)
        else:
            players = self.sort_by_score(players, games)
        return players

    def sort_by_rating(self, players):
        return sorted(players, key=lambda player: player.rating)

    def sort_by_score(self, players, games):
        for game in games:
            if game.winner is not None:
                player = getattr(game, game.winner)
                player.add_score(self.__WIN_SCORE)
            else:
                game.white.add_score(self.__DRAW_SCORE)
                game.black.add_score(self.__DRAW_SCORE)
        return sorted(players, key=lambda player: player.score)