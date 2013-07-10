# -*- encoding: utf-8 -*-
from functools import wraps
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.shortcuts import redirect


class CreateOnlyFieldsMixin(object):
    create_only_fields = ()

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields if obj is None else self.create_only_fields or ()


class AdminURLMixin(object):
    def get_admin_url_pattern(self, action='change'):
        ct = ContentType.objects.get_for_model(self.model)
        return 'admin:%s_%s_%s' % (ct.app_label, ct.model, action)


class ChangeFormActionsMixin(AdminURLMixin):
    add_form_template = 'admin/change_form.html'
    change_form_template = 'admin/custom_change_form.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        actions = self.get_actions(request)
        if actions:
            action_form = self.action_form(auto_id=None)
            action_form.fields['action'].choices = filter(
                lambda (name, desc): getattr(getattr(self, name, None), 'change_form_action', False),
                self.get_action_choices(request))
        else:
            action_form = None
        changelist_url = urlresolvers.reverse(self.get_admin_url_pattern('changelist'))
        return super(ChangeFormActionsMixin, self).change_view(request, object_id, form_url, extra_context={
            'action_form': action_form,
            'changelist_url': changelist_url
        })


class ForbidAddMixin(object):
    def has_add_permission(self, request, obj=None):
        return False


class ForbidChangeMixin(object):
    def has_change_permission(self, request, obj=None):
        return False


class ForbidDeleteMixin(object):
    def has_delete_permission(self, request, obj=None):
        return False


def change_form_action(action):
    @wraps(action)
    def closure(self, request, queryset):
        action(self, request, queryset)
        return redirect(urlresolvers.reverse(self.get_admin_url_pattern(), args=(queryset[0].pk,)))

    closure.change_form_action = True
    return closure