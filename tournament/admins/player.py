# -*- encoding: utf-8 -*-
from django.contrib import admin

from ..models import Player


class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'rating', 'fide_id', 'fide_games', 'is_fide_newbie')


admin.site.register(Player, PlayerAdmin)
