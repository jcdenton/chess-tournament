# -*- encoding: utf-8 -*-
from django.contrib import admin, messages
from django.core import urlresolvers

from ..models import Round, RefereeProfile, Tournament
from .utils import ChangeFormActionsMixin, CustomStackedInline, ForbidAddMixin, \
    change_form_action, get_fk_field_link, owner_required


class RoundInline(ForbidAddMixin, CustomStackedInline):
    model = Round
    extra = 0


class TournamentAdmin(ChangeFormActionsMixin, admin.ModelAdmin):
    list_display = ('name', 'referee_link', 'players_count', 'start_date', 'end_date', 'finished')
    list_filter = ('referee', 'finished', 'start_date')
    search_fields = ('name',)
    filter_horizontal = ('players',)
    create_only_fields = ('players', 'referee')
    readonly_fields = ('player_list', 'referee_link')
    change_only_fields = ('player_list', 'referee_link')
    inlines = (RoundInline,)
    actions = ('next_round',)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(TournamentAdmin, self).get_readonly_fields(request, obj)
        if obj is None and readonly_fields is not None:
            readonly_fields = set(readonly_fields) - set(self.change_only_fields)
        return readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        kwargs.update(exclude=self.change_only_fields if obj is None else self.create_only_fields)
        return super(TournamentAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'referee':
            kwargs.update(queryset=RefereeProfile.objects.filter(user=request.user))
        return super(TournamentAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def player_list(self, obj):
        return u', '.join([
            u'<a href="%s">%s</a>' % (urlresolvers.reverse('admin:tournament_player_change', args=(player.pk,)), player)
            for player in obj.players.all()])

    player_list.short_description = u'Players'
    player_list.allow_tags = True

    referee_link = get_fk_field_link('refereeprofile', u'Referee', 'referee')

    @owner_required('referee.user')
    def has_change_permission(self, request, obj=None):
        return super(TournamentAdmin, self).has_change_permission(request, obj)

    @owner_required('referee.user')
    def has_delete_permission(self, request, obj=None):
        return super(TournamentAdmin, self).has_delete_permission(request, obj)

    @change_form_action
    def next_round(self, request, queryset):
        try:
            queryset[0].finish_current_round()
        except UserWarning, e:
            self.message_user(request, e, level=messages.ERROR)


admin.site.register(Tournament, TournamentAdmin)
