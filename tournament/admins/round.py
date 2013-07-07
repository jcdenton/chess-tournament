# -*- encoding: utf-8 -*-
from django.contrib import admin
from ..models import Game, Round


class GameInline(admin.StackedInline):
    model = Game
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RoundAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament', 'games_count')
    readonly_fields = ('tournament',)
    inlines = (GameInline,)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Round, RoundAdmin)
