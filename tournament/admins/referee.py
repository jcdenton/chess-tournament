# -*- encoding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.models import User
from ..models import RefereeProfile


class RefereeProfileAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'user':
            kwargs.update(queryset=User.objects.filter(pk=request.user.pk))
        return super(RefereeProfileAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(RefereeProfile, RefereeProfileAdmin)