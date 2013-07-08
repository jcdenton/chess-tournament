# -*- encoding: utf-8 -*-
from random import sample
import math

from models import Game, Side, Score


class EloRatingCalculator(object):
    def calculate_ratings(self, tournament):
        scores = tournament.score_set.all()
        for game in tournament.get_games():
            scores = self.get_game_scores(game)
            game.white.rating = self.get_new_rating(game.white, game.black, scores[Side.WHITE])
            game.black.rating = self.get_new_rating(game.black, game.white, scores[Side.BLACK])

    def get_new_rating(self, player, opponent, score):
        return player.rating + self.get_k(player) * (score - self.get_expectation(player, opponent))

    def get_k(self, player):
        if player.rating >= 2400:
            return 10
        elif player.is_fide_newbie():
            return 30
        else:
            return 15

    def get_expectation(self, player, opponent):
        return 1 / (1 + 10 ** ((opponent.rating - player.rating) / 400))

    def get_game_scores(self, game):
        if game.winner == Side.WHITE:
            white_score = Score.WIN
            black_score = Score.DEFEAT
        elif game.winner == Side.BLACK:
            white_score = Score.DEFEAT
            black_score = Score.WIN
        else:
            white_score = Score.DRAW
            black_score = Score.DRAW
        return {
            Side.WHITE: white_score,
            Side.BLACK: black_score
        }


class SwissSystemTournament(object):
    def get_round_count(self, tournament):
        return round(math.log(tournament.players.count(), 2)) + round(math.log(tournament.players.count(), 2))

    def finish_round(self, tournament):
        latest_round = tournament.get_latest_round()
        if not latest_round.is_finished():
            raise UserWarning('Round "%s" isn\'t finished yet' % latest_round)

    def add_next_round(self, tournament, name):
        if self.get_round_count(tournament) <= tournament.round_set.count():
            pass
        past_games = tournament.get_games()
        players = self.sort_players(tournament.players[:], past_games)
        r = tournament.round_set.create(name=name, tournament=tournament)
        games = [Game(round=r, **self.define_colors(pair)) for pair in self.make_pairs(players)]
        r.game_set.add(games)

    def make_pairs(self, players):
        pairs = self.pair_group(players)

        players_count = len(players)
        if players_count % 2 != 0:
            pairs.append((players[players_count - 1], None))

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
        """
        Sorts the players by their rating in the first round and by current tournament score in all the following ones.
        """
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
                player.add_score(Score.WIN)
            else:
                game.white.add_score(Score.DRAW)
                game.black.add_score(Score.DRAW)
        return sorted(players, key=lambda player: player.score)