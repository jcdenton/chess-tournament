# -*- encoding: utf-8 -*-
from django.contrib import admin

from ..models import Game, Score
from utils import ForbidAddMixin, ForbidDeleteMixin


class ScoreInline(ForbidAddMixin, ForbidDeleteMixin, admin.StackedInline):
    model = Score
    extra = 0


class GameAdmin(ForbidAddMixin, admin.ModelAdmin):
    inlines = (ScoreInline,)


admin.site.register(Game, GameAdmin)
