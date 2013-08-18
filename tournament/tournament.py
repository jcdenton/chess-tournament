# -*- encoding: utf-8 -*-
from datetime import datetime
import itertools
import math
import operator
import random

from django.db import models

from .models import Side, Scores


class EloRatingMixin(object):
    def update_scores(self):
        self.score_set.clear()
        self.score_set.create(player=self.white, side=Side.WHITE, score=self.get_side_score(Side.WHITE),
                              rating_delta=self.get_rating_delta(self.white, self.black,
                                                                 self.get_side_score(Side.WHITE)))
        self.score_set.create(player=self.black, side=Side.BLACK, score=self.get_side_score(Side.BLACK),
                              rating_delta=self.get_rating_delta(self.black, self.white,
                                                                 self.get_side_score(Side.BLACK)))

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
    def progress(self, next_round_name=None):
        self.finish_current_round()

        if self.round_set.count() < self.max_round_count():
            self.start_next_round(next_round_name)
        else:
            self.finish_tournament()

    def max_round_count(self):
        return round(math.log(self.players.count(), 2)) + round(math.log(self.players.count(), 2))

    def finish_tournament(self):
        self.update_ratings()
        self.finished = True
        self.end_date = datetime.now()
        self.save()

    def finish_current_round(self):
        if self.finished:
            raise UserWarning(u'The tournament "%s" is already finished' % self)
        if self.get_started_games().count() != 0:
            raise UserWarning(u'Some games are not finished yet')

        current_round = self.get_latest_round()
        if current_round is not None:
            self.update_round_scores(current_round)

    def update_round_scores(self, current_round):
        """
        :param current_round: currently latest Round
        :type current_round: Round
        """
        if not current_round.finished:
            raise UserWarning(u'"%s" is not finished yet' % current_round)

        for game in current_round.game_set.all():
            game.update_scores()

    def start_next_round(self, next_round_name):
        """
        :param next_round_name: next round name
        :type next_round_name: basestring
        """
        if next_round_name is None:
            next_round_name = u'Round %s' % str(self.round_set.count() + 1)

        next_round = self.round_set.create(name=next_round_name, start_date=datetime.now())
        for pair in self.pair_players():
            next_round.game_set.create(start_date=datetime.now(), **self.map_colors(pair))

    def update_ratings(self):
        """
        Updates players ratings based on this tournament resulting scores.
        """
        for player in self.players.all():
            player.rating += self.get_player_scores(player).aggregate(models.Sum('rating_delta'))
            player.save()

    def pair_players(self):
        """
        Returns list of player pairs.
        :returns: list of player pairs
        :rtype: list
        """
        return list(itertools.chain.from_iterable(map(self.pair_players_group,
                                                      self.normalize_groups(self.group_players()))))

    def normalize_groups(self, groups):
        """
        Normalizes groups by making them having even number of players each (except the last one).
        :param groups: list of groups
        :type groups: list
        :returns: normalized list of groups
        :rtype: list
        """
        for (i, group) in enumerate(groups):
            if len(group) % 2 != 0 and i < len(groups) - 1:
                groups[i + 1].insert(0, group.pop())
        return groups

    def group_players(self):
        """
        Groups players by current tournament score and sorts them by score/rating inside those groups.
        :returns: list of lists of players
        :rtype: list
        """
        return [self.sort_players(igroup) for (score, igroup) in sorted(
            itertools.groupby(self.players.all(), self.get_player_summary_score),
            reverse=True, key=operator.itemgetter(0))]

    def get_player_summary_score(self, player):
        return self.get_player_scores(player).aggregate(models.Sum('score')).get('score__sum') or 0.0

    def get_tournament_pairs(self):
        """
        Returns permutations of pairs already been played in this tournament.
        :rtype: set
        """
        pairs = set((game.white, game.black) for game in self.get_games().all())
        return pairs | set(map(reversed, pairs))

    def pair_players_group(self, group):
        """
        Returns list of player pairs.
        :param group: list of grouped players
        :type group: list
        :rtype: list
        """
        pairs = []
        group = group[:]
        players_count = len(group)
        opponents = group[players_count:] + group[:players_count]
        excluding_permutations = self.get_tournament_pairs()

        for (i, player) in enumerate(group):
            opponent = opponents[i]
            if (player, opponent) in excluding_permutations:
                opponent = next(filter(lambda o: o is not player and (player, o) not in excluding_permutations,
                                       opponents))
                excluding_permutations.update({(player, opponent), (opponent, player)})
            pairs.append((player, opponent))

        return pairs

    def get_played_sides(self, pair):
        """
        Returns dict of dicts, countaining played games number for each side: { player: { color: games_count } }.
        :param pair: pair of players
        :type pair: tuple
        :rtype: dict
        """
        past_games = {}

        for player in pair:
            if player is not None:
                past_games_white = player.game_set_white.filter(round__tournament=self).count()
                past_games_black = player.game_set_black.filter(round__tournament=self).count()
            past_games.update({player: {Side.WHITE: past_games_white, Side.BLACK: past_games_black}})

        return past_games

    def map_colors(self, pair):
        """
        Returns dict of { color: player } entries.
        :param pair: pair of players
        :type pair: tuple
        :rtype: dict
        """
        past_games = self.get_played_sides(pair)

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

    def sort_players(self, players=None):
        """
        Sorts the players by their rating in the first round and by current tournament score in all the following ones.
        :param players: players iterable. If missing - will use self.players.all()
        :type players: Iterable
        :rtype: list
        """
        if players is None:
            players = self.players.all()
        if self.get_finished_games().count() == 0:
            compare_key = operator.attrgetter('rating')
        else:
            compare_key = self.get_player_summary_score
        return sorted(players, reverse=True, key=compare_key)
