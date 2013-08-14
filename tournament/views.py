# -*- encoding: utf-8 -*-
from django.views import generic

from .models import Tournament


class TournamentListView(generic.ListView):
    context_object_name = 'tournaments'

    def get_queryset(self):
        return Tournament.objects.order_by('-start_date')


class TournamentDetailView(generic.DetailView):
    model = Tournament
    context_object_name = 'tournament'
