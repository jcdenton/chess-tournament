# -*- encoding: utf-8 -*-
from django.contrib import admin

from ..models import RefereeProfile, Tournament
from utils import ForbidAddMixin, ForbidDeleteMixin, ForbidChangeMixin


class TournamentInline(ForbidAddMixin, ForbidChangeMixin, admin.TabularInline):
    model = Tournament
    extra = 0


class RefereeProfileAdmin(ForbidAddMixin, ForbidDeleteMixin, admin.ModelAdmin):
    readonly_fields = ('user',)
    inlines = (TournamentInline,)


admin.site.register(RefereeProfile, RefereeProfileAdmin)