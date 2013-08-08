# -*- encoding: utf-8 -*-
from django.contrib import admin

from ..models import RefereeProfile
from .utils import ForbidAddMixin, ForbidDeleteMixin


class RefereeProfileAdmin(ForbidAddMixin, ForbidDeleteMixin, admin.ModelAdmin):
    list_display = ('__unicode__', 'user')
    readonly_fields = ('user',)


admin.site.register(RefereeProfile, RefereeProfileAdmin)