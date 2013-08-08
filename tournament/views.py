# -*- encoding: utf-8 -*-
from django.views import generic

from .models import Tournament


class TournamentsView(generic.ListView):
    context_object_name = 'tournaments'

    def get_queryset(self):
        return Tournament.objects.order_by('-start_date')