# -*- encoding: utf-8 -*-
from functools import wraps
from django.contrib import admin, messages

from ..models import Round, RefereeProfile, Tournament
from utils import CreateOnlyFieldsMixin, ChangeFormActionsMixin, change_form_action, ForbidAddMixin, \
    ForbidDeleteMixin


class RoundInline(ForbidAddMixin, admin.StackedInline):
    template = 'admin/round_stacked_inline.html'
    model = Round
    extra = 0


def referee_required(permission_check_method):
    @wraps(permission_check_method)
    def closure(self, request, obj=None):
        if permission_check_method(self, request, obj):
            if obj is not None and request.user != obj.referee.user:
                return False
            return True
        return False

    return closure


class TournamentAdmin(CreateOnlyFieldsMixin, ChangeFormActionsMixin, admin.ModelAdmin):
    list_display = ('name', 'referee', 'players_count', 'start_date', 'end_date', 'finished')
    filter_horizontal = ('players',)
    create_only_fields = ('players',)
    inlines = (RoundInline,)
    actions = ('next_round',)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'referee':
            kwargs.update(queryset=RefereeProfile.objects.filter(user=request.user))
        return super(TournamentAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    @referee_required
    def has_change_permission(self, request, obj=None):
        return super(TournamentAdmin, self).has_change_permission(request, obj)

    @referee_required
    def has_delete_permission(self, request, obj=None):
        return super(TournamentAdmin, self).has_delete_permission(request, obj)

    @change_form_action
    def next_round(self, request, queryset):
        try:
            queryset[0].finish_round()
        except UserWarning, e:
            self.message_user(request, e, level=messages.ERROR)


admin.site.register(Tournament, TournamentAdmin)
