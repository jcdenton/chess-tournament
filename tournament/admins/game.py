# -*- encoding: utf-8 -*-
from django.contrib import admin

from ..models import Game, Score
from .utils import ForbidAddMixin, ForbidDeleteMixin, get_fk_field_link, CustomStackedInline


class ScoreInline(ForbidAddMixin, ForbidDeleteMixin, CustomStackedInline):
    model = Score
    extra = 0


class GameAdmin(ForbidAddMixin, admin.ModelAdmin):
    exclude = ('round',)
    readonly_fields = ('round_link',)
    inlines = (ScoreInline,)

    round_link = get_fk_field_link('round', 'Round', 'round')


admin.site.register(Game, GameAdmin)
