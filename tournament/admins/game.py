# -*- encoding: utf-8 -*-
from django.contrib import admin

from ..models import Game, Score
from .utils import ForbidAddMixin, get_fk_field_link, CustomStackedInline


class ScoreInline(ForbidAddMixin, CustomStackedInline):
    model = Score
    extra = 0


class GameAdmin(ForbidAddMixin, admin.ModelAdmin):
    list_display = ('__unicode__', 'white', 'black', 'winner', 'round_link', 'start_date', 'end_date')
    exclude = ('round',)
    readonly_fields = ('round_link',)
    inlines = (ScoreInline,)
    search_fields = ('tournament',)

    round_link = get_fk_field_link('round', 'Round', 'round')


admin.site.register(Game, GameAdmin)
