# -*- encoding: utf-8 -*-


class EloRatingCalculator(object):
    def __init__(self):
        pass

    def calculate_ratings(self, tournament):
        pass

    def get_new_rating(self, player, score):
        return player.rating + self._get_k(player) * (score - self._get_expectation())

    def _get_k(self, player):
        if player.rating >= 2400:
            return 10
        elif player.is_fide_newbie():
            return 30
        else:
            return 15

    def _get_expectation(self, player, opponent):
        return 1 / (1 + 10 ** ((opponent.rating - player.rating) / 400))
