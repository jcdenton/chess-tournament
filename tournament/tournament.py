# -*- encoding: utf-8 -*-
from datetime import datetime
from itertools import groupby, chain
import math
import operator
import random

from django.db.models import Sum

from .models import Side, Scores


class EloRatingMixin(object):
    def update_scores(self):
        self.score_set.clear()
        self.score_set.create(game=self, player=self.white, side=Side.WHITE, score=self.get_side_score(Side.WHITE),
                              rating_delta=self.get_rating_delta(self.white, self.black, self.get_side_score(Side.WHITE)))
        self.score_set.create(game=self, player=self.black, side=Side.BLACK, score=self.get_side_score(Side.BLACK),
                              rating_delta=self.get_rating_delta(self.black, self.white, self.get_side_score(Side.BLACK)))

    def get_side_score(self, side):
        if self.winner == side:
            return Scores.WIN
        elif self.winner is None:
            return Scores.DRAW
        else:
            return Scores.DEFEAT

    def get_rating_delta(self, player, opponent, score):
        return self.get_k(player) * (score - self.get_expectation(player, opponent))

    def get_k(self, player):
        if player.rating >= 2400:
            return 10
        elif player.is_fide_newbie():
            return 30
        else:
            return 15

    def get_expectation(self, player, opponent):
        return 1 / (1 + 10 ** ((opponent.rating - player.rating) / 400))


class SwissSystemMixin(object):
    def finish_current_round(self, next_round_name=None):
        if self.finished:
            raise UserWarning(u'The tournament "%s" is already finished' % self)

        if self.get_started_games().count() != 0:
            raise UserWarning(u'Some games are not finished yet')

        current_round = self.get_latest_round()
        if current_round is not None:
            if not current_round.finished:
                raise UserWarning(u'Round "%s" is not finished yet' % current_round)
            for game in current_round.game_set.all():
                game.update_scores()

        if self.round_set.count() < self.max_round_count():
            self.start_next_round(next_round_name)
        else:
            self.finish_tournament()

    def finish_tournament(self):
        self.update_ratings()
        self.finished = True
        self.end_date = datetime.now()
        self.save()

    def start_next_round(self, next_round_name):
        if next_round_name is None:
            next_round_name = u'Round %s' % str(self.round_set.count() + 1)
        r = self.round_set.create(name=next_round_name, tournament=self, start_date=datetime.now())
        for pair in self.pair_players():
            r.game_set.create(round=r, start_date=datetime.now(), **self.map_colors(pair))

    def max_round_count(self):
        return round(math.log(self.players.count(), 2)) + round(math.log(self.players.count(), 2))

    def update_ratings(self):
        for player in self.players.all():
            for score in self.get_player_scores(player):
                player.rating += score.rating_delta
            player.save()

    def pair_players(self):
        return list(chain(map(self.pair_players_group, self.group_players())))

    def group_players(self):
        groups = []
        player = None

        for (score, igroup) in groupby(self.get_sorted_players(), self.get_player_summary_score):
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

    def get_player_summary_score(self, player):
        return self.get_player_scores(player).aggregate(Sum('score'))

    def pair_players_group(self, group):
        players_count = len(group)

        pairs = [(group[i], group[players_count / 2 + i]) for i in range(players_count / 2)]
        if players_count % 2 != 0:
            pairs.append((group[players_count - 1], None))

        return pairs

    def map_colors(self, pair):
        past_games = {}
        for player in pair:
            if player is not None:
                past_games_white = player.game_set_white.filter(round__tournament=self).count()
                past_games_black = player.game_set_black.filter(round__tournament=self).count()
            past_games.update({player: {Side.WHITE: past_games_white, Side.BLACK: past_games_black}})

        if past_games[pair[0]][Side.WHITE] < past_games[pair[1]][Side.WHITE]:
            resulting_pair = pair
        elif past_games[pair[0]][Side.BLACK] < past_games[pair[1]][Side.BLACK]:
            resulting_pair = reversed(pair)
        else:
            resulting_pair = random.sample(pair, 2)

        return dict(zip(
            (Side.WHITE, Side.BLACK),
            resulting_pair
        ))

    def get_sorted_players(self):
        """
        Sorts the players by their rating in the first round and by current tournament score in all the following ones.
        """
        if self.get_games().count() == 0:
            compare_key = operator.attrgetter('rating')
        else:
            compare_key = self.get_player_summary_score
        return sorted(self.players.all(), reverse=True, key=compare_key)