# -*- encoding: utf-8 -*-
from django.contrib import admin
from ..models import Player


class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'rating')


admin.site.register(Player, PlayerAdmin)
