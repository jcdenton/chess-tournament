# -*- encoding: utf-8 -*-
from datetime import datetime
from itertools import groupby
import math
import random
from django.db.models import Sum

from models import Side, Scores


class EloRatingMixin(object):
    def update_scores(self):
        self.score_set.clear()
        self.score_set.create(game=self, player=self.white, side=Side.WHITE, score=self._get_score(Side.WHITE),
                              rating_delta=self._get_rating_delta(self.white, self.black, self._get_score(Side.WHITE)))
        self.score_set.create(game=self, player=self.black, side=Side.BLACK, score=self._get_score(Side.BLACK),
                              rating_delta=self._get_rating_delta(self.black, self.white, self._get_score(Side.BLACK)))

    def _get_score(self, side):
        if self.winner == side:
            return Scores.WIN
        elif self.winner is None:
            return Scores.DRAW
        else:
            return Scores.DEFEAT

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


class SwissSystemMixin(object):
    def finish_round(self, next_round_name=None):
        if self.finished:
            raise UserWarning(u'The tournament "%s" is already finished' % self)

        if self.get_games().count() != 0 and self.get_started_games().count() != 0:
            raise UserWarning(u'Some games are not finished yet')

        latest_round = self.get_latest_round()
        if latest_round is not None:
            if not latest_round.finished:
                raise UserWarning(u'Round "%s" is not finished yet' % latest_round)
            for game in latest_round.game_set.all():
                game.update_scores()

        if self.round_set.count() < self._max_round_count():
            self._update_ratings()
            if next_round_name is None:
                next_round_name = u'Round %s' % str(self.round_set.count() + 1)
            self._next_round(next_round_name)

    def _next_round(self, name):
        r = self.round_set.create(name=name, tournament=self, start_date=datetime.now())
        for pair in self._pair_players():
            r.game_set.create(round=r, start_date=datetime.now(), **self._get_colors(pair))

    def _max_round_count(self):
        return round(math.log(self.players.count(), 2)) + round(math.log(self.players.count(), 2))

    def _update_ratings(self):
        for player in self.players.all():
            for score in self.get_player_scores(player):
                player.ratin += score.rating_delta
            player.save()

    def _pair_players(self):
        pairs = []
        for group in self._group_players():
            pairs.extend(self._pair_group(group))
        return pairs

    def _group_players(self):
        groups = []
        player = None
        for (score, igroup) in groupby(self._sort_players(), self._get_player_summary_score):
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
        def get_key(player):
            return player.pk if player is not None else None

        past_games = {}
        for player in pair:
            if player is not None:
                past_games_white = player.game_set_white.filter(round__tournament=self).count()
                past_games_black = player.game_set_black.filter(round__tournament=self).count()
            past_games.update({get_key(player): {Side.WHITE: past_games_white, Side.BLACK: past_games_black}})
        print past_games
        if past_games[get_key(player)][Side.WHITE] < past_games[get_key(player)][Side.WHITE]:
            result = pair
        elif past_games[get_key(player)][Side.BLACK] < past_games[get_key(player)][Side.BLACK]:
            result = reversed(pair)
        else:
            result = random.sample(pair, 2)

        print dict(zip(
            (Side.WHITE, Side.BLACK),
            result
        ))
        return dict(zip(
            (Side.WHITE, Side.BLACK),
            result
        ))

    def _sort_players(self):
        """
        Sorts the players by their rating in the first round and by current tournament score in all the following ones.
        """
        print self.get_games().all()
        if self.get_games().count() == 0:
            return sorted(self.players.all(), reverse=True, key=lambda player: player.rating)
        else:
            return sorted(self.players.all(), reverse=True,
                          key=lambda player: player.score_set.filter(game__in=self.get_games().all()))