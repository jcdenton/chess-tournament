# -*- encoding: utf-8 -*-
from datetime import datetime
from functools import partial
from itertools import groupby
import math
import random
from django.db.models import Sum

from models import Game, Side, Score, Tournament


class EloRatingMixin(object):
    def update_scores(self):
        white_score = Score(game=self, player=self.white, side=Side.WHITE, score=self._get_score(Side.WHITE),
                            rating_delta=self._get_rating_delta(self.white, self.black, self._get_score(Side.WHITE)))
        black_score = Score(game=self, player=self.black, side=Side.BLACK, score=self._get_score(Side.BLACK),
                            rating_delta=self._get_rating_delta(self.black, self.white, self._get_score(Side.BLACK)))
        self.score_set.clear()
        self.score_set.add([white_score, black_score])

    def _get_score(self, side):
        if self.winner == side:
            return Score.WIN
        elif self.winner is None:
            return Score.DRAW
        else:
            return Score.DEFEAT

    def _get_rating_delta(self, player, opponent, score):
        return self._get_k(player) * (score - self._get_expectation(player, opponent))

    def _get_k(self, player):
        if player.rating >= 2400:
            return 10
        elif player.is_fide_newbie():
            return 30
        else:
            return 15

    def _get_expectation(self, player, opponent):
        return 1 / (1 + 10 ** ((opponent.rating - player.rating) / 400))


class SwissSystemMixin(Tournament):
    def finish_round(self, name):
        if self.finished:
            raise UserWarning(u'The tournament "%s" is already finished' % self)

        if self.get_started_games().count() != 0:
            raise UserWarning(u'Some games are not finished yet')

        latest_round = self.get_latest_round()
        if not latest_round.is_finished():
            raise UserWarning(u'Round "%s" is not finished yet' % latest_round)
        for game in latest_round.game_set.all():
            game.update_scores()

        if self.round_set.count() < self.max_round_count():
            self._next_round(name)
        else:
            self._update_ratings()

    def _next_round(self, name):
        r = self.round_set.create(name=name, tournament=self)
        new_games = [Game(round=r, start_date=datetime.now(), **self._get_colors(pair)) for pair in self._pair_players(players)]
        r.game_set.add(new_games)

    def max_round_count(self):
        return round(math.log(self.players.count(), 2)) + round(math.log(self.players.count(), 2))

    def _update_ratings(self):
        for player in self.players:
            for score in self.get_player_scores(player):
                player.ratin += score.rating_delta
            player.save()

    def _pair_players(self, players):
        pairs = []
        for group in self._group_players():
            pairs.append(self._pair_group(group))
        return pairs

    def _group_players(self):
        groups = []
        player = None
        players = self._sort_players()
        for (score, igroup) in groupby(players, partial(self._get_player_summary_score, self)):
            group = list(igroup)
            if player is not None:
                group.insert(0, player)
                player = None
            if len(group) % 2 != 0:
                player = group.pop()
            groups.append(group)
        if player is not None:
            groups.append([player])
        return groups

    def _get_player_summary_score(self, player):
        return self.get_player_scores(player).aggregate(Sum('score'))

    def _pair_group(self, players_group):
        players_count = len(players_group)
        pairs = [(players_group[i], players_group[players_count / 2 + i]) for i in range(players_count / 2)]
        if players_count % 2 != 0:
            pairs.append((players_group[players_count - 1], None))
        return pairs

    def _get_colors(self, pair):
        past_games = {}
        for player in pair:
            past_games_white = player.game_set_white.order_by('-start_date', '-end_date', '-id').count() \
                if player is not None else 0
            past_games_black = player.game_set_black.order_by('-start_date', '-end_date', '-id').count() \
                if player is not None else 0
            past_games.update(player, {Side.WHITE: past_games_white, Side.BLACK: past_games_black})

        if past_games[pair[0]][Side.WHITE] < past_games[pair[1]][Side.WHITE]:
            result = pair
        elif past_games[pair[0]][Side.BLACK] < past_games[pair[1]][Side.BLACK]:
            result = reversed(pair)
        else:
            result = random.sample(pair, 2)

        return dict(zip(
            (Side.WHITE, Side.BLACK),
            result
        ))

    def _sort_players(self):
        """
        Sorts the players by their rating in the first round and by current tournament score in all the following ones.
        """
        games = self.get_games()
        if len(games) == 0:
            players = sorted(self.players, key=lambda player: player.rating)
        else:
            players = sorted(self.players, key=lambda player: player.score_set.filter(game__tournament_id=self.pk))
        return players
