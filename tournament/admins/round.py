# -*- encoding: utf-8 -*-
from django.contrib import admin

from ..models import Game, Round
from .utils import ForbidAddMixin, CustomStackedInline, get_fk_field_link


class GameInline(ForbidAddMixin, CustomStackedInline):
    model = Game
    extra = 0


class RoundAdmin(ForbidAddMixin, admin.ModelAdmin):
    list_display = ('name', 'tournament_link', 'games_count')
    inlines = (GameInline,)
    exclude = ('tournament',)
    readonly_fields = ('tournament_link',)

    tournament_link = get_fk_field_link('tournament', 'Tournament', 'tournament')


admin.site.register(Round, RoundAdmin)
