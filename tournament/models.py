# -*- encoding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
import django_countries


class Side(object):
    WHITE = 'white'
    BLACK = 'black'


class Scores(object):
    WIN = 1.0
    DRAW = 0.5
    DEFEAT = 0.0


class RefereeProfile(models.Model):
    user = models.OneToOneField(User)

    def __unicode__(self):
        result = u' '.join((self.user.first_name, self.user.last_name))
        return result if not result.isspace() else self.user.__unicode__()

    @staticmethod
    def user_post_save(sender, instance, created, **kwargs):
        if created:
            p = RefereeProfile()
            p.user = instance
            p.save()


post_save.connect(RefereeProfile.user_post_save, sender=User)


class Player(models.Model):
    name = models.CharField(max_length=128)
    country = django_countries.CountryField()
    rating = models.IntegerField()
    fide_id = models.IntegerField(blank=True, null=True, default=None)
    fide_games = models.IntegerField(blank=True, null=True, default=None)

    def is_fide_newbie(self):
        return self.fide_id is not None and self.fide_games is not None and self.fide_games <= 30

    is_fide_newbie.boolean = True

    def __unicode__(self):
        return u'%s [%s]' % (self.name, self.rating)


from tournament import SwissSystemMixin


class Tournament(models.Model, SwissSystemMixin):
    name = models.CharField(max_length=128)
    players = models.ManyToManyField(Player)
    referee = models.ForeignKey(RefereeProfile)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    finished = models.BooleanField()

    def players_count(self):
        return self.players.count()

    def get_games(self):
        return Game.objects.filter(round__in=self.round_set.all())

    def get_started_games(self):
        return self.get_games().filter(finished=False)

    def get_latest_round(self):
        try:
            rounds = self.round_set.order_by('-start_date', '-id')
            if rounds[0].total_games_count() == 0 and rounds.count() > 1:
                return rounds[1]
            else:
                return rounds[0]
        except IndexError:
            return None

    def get_player_scores(self, player):
        return player.score_set.filter(game__in=self.get_games().all())

    def __unicode__(self):
        return self.name


class Round(models.Model):
    name = models.CharField(max_length=128)
    tournament = models.ForeignKey(Tournament)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    finished = models.BooleanField()

    def games_count(self):
        return '%s / %s' % (self.finished_games_count(), self.total_games_count())

    def total_games_count(self):
        return self.game_set.count()

    def finished_games_count(self):
        return self.game_set.filter(finished=True).count()

    def started_games_count(self):
        return self.game_set.filter(finished=False).count()

    def __unicode__(self):
        return u'%s - %s' % (self.tournament, self.name)


from tournament import EloRatingMixin


class Game(EloRatingMixin, models.Model):
    WINNER_CHOICES = (
        (Side.WHITE, 'White'),
        (Side.BLACK, 'Black'),
        (None, 'Draw')
    )
    white = models.ForeignKey(Player, blank=True, null=True, related_name='game_set_white')
    black = models.ForeignKey(Player, blank=True, null=True, related_name='game_set_black')
    finished = models.BooleanField()
    round = models.ForeignKey(Round)
    winner = models.CharField(blank=True, null=True, max_length=5, choices=WINNER_CHOICES, default=None)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return u'%s vs. %s' % (self.white, self.black)


class Score(models.Model):
    SIDE_CHOICES = (
        (Side.WHITE, 'White'),
        (Side.BLACK, 'Black')
    )
    player = models.ForeignKey(Player)
    side = models.CharField(max_length=5, choices=SIDE_CHOICES)
    game = models.ForeignKey(Game)
    score = models.FloatField(default=0.0)
    rating_delta = models.FloatField(default=0.0)

    def __unicode__(self):
        return u'%s: %.1f (%+1.1f)' % (self.player, self.score, self.rating_delta)
