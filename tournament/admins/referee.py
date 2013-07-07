# -*- encoding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.models import User
from ..models import RefereeProfile


class UserInline(admin.StackedInline):
    model = User


class RefereeProfileAdmin(admin.ModelAdmin):
    inlines = (UserInline,)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(RefereeProfile, RefereeProfileAdmin)