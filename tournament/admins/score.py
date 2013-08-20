# -*- encoding: utf-8 -*-
from django.contrib import admin

from ..models import Score
from .utils import ForbidAddMixin


class ScoreAdmin(ForbidAddMixin, admin.ModelAdmin):
    pass

admin.site.register(Score, ScoreAdmin)
