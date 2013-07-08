# -*- encoding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
import django_countries


class RefereeProfile(models.Model):
    user = models.OneToOneField(User)

    def __unicode__(self):
        return ' '.join((self.user.first_name, self.user.last_name)) \
            if self.user.first_name is not None and self.user.last_name is not None \
            else super(RefereeProfile, self).__unicode__()

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


class Tournament(models.Model):
    name = models.CharField(max_length=128)
    players = models.ManyToManyField(Player)
    referee = models.ForeignKey(RefereeProfile)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    def players_count(self):
        return self.players.count()

    def get_games(self):
        # return [game for r in self.round_set for game in r.game_set]
        return Game.objects.filter(round__in=self.round_set.all())

    def is_finished(self):
        # return len([r for r in self.round_set if not r.is_finished()]) == 0
        return self.get_games().filter(status=Status.STARTED).count() == 0
    is_finished.boolean = True

    def get_latest_round(self):
        try:
            return self.round_set.order_by('-start_date', '-end_date', '-name', '-id')[0]
        except IndexError:
            return None

    def __unicode__(self):
        return self.name


class Round(models.Model):
    name = models.CharField(max_length=128)
    tournament = models.ForeignKey(Tournament)

    def games_count(self):
        return '%s / %s' % (self.finished_games_count(), self.total_games_count())

    def total_games_count(self):
        return self.game_set.count()

    def finished_games_count(self):
        # return len([game for game in self.game_set if game.is_finished()])
        return self.game_set.filter(status=Status.FINISHED).count()

    def started_games_count(self):
        return self.game_set.filter(status=Status.STARTED).count()

    def is_finished(self):
        # return len([game for game in self.game_set if not game.is_finished()]) == 0
        return self.started_games_count() == 0
    is_finished.boolean = True

    def __unicode__(self):
        return u'%s - %s' % (self.tournament, self.name)


class Status(object):
    STARTED = 'started'
    FINISHED = 'finished'
    DRAW = 'draw'


class Side(object):
    WHITE = 'white'
    BLACK = 'black'


class Game(models.Model):
    STATUS_CHOICES = (
        (Status.STARTED, 'Started'),
        (Status.FINISHED, 'Finished')
    )
    WINNER_CHOICES = (
        (Side.WHITE, 'White'),
        (Side.BLACK, 'Black'),
        (None, 'DRAW')
    )
    white = models.ForeignKey(Player, related_name='game_set_white')
    black = models.ForeignKey(Player, related_name='game_set_black')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=Status.STARTED)
    round = models.ForeignKey(Round)
    winner = models.CharField(max_length=5, choices=WINNER_CHOICES, default=None)
    start_date = models.DateTimeField(auto_now_add=True, editable=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def is_finished(self):
        return self.status == self.FINISHED
    is_finished.boolean = True

    def __unicode__(self):
        return u'%s vs. %s' % (self.white, self.black)


class Score(models.Model):
    tournament = models.ForeignKey(Tournament)
    player = models.ForeignKey(Player)
    game = models.ForeignKey(Game)
    score = models.FloatField()

    def add_score(self, score):
        self.score += score
        self.save()

    def __unicode__(self):
        return u'%s - %2.2f' % (self.player, self.score)
