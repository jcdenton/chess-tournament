# -*- encoding: utf-8 -*-
from django.contrib import admin

from ..models import Game, Round
from utils import ForbidAddMixin, ForbidDeleteMixin


class GameInline(ForbidAddMixin, admin.StackedInline):
    model = Game
    extra = 0


class RoundAdmin(ForbidAddMixin, admin.ModelAdmin):
    list_display = ('name', 'tournament', 'games_count')
    readonly_fields = ('tournament',)
    inlines = (GameInline,)


admin.site.register(Round, RoundAdmin)
