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

    def get_context_data(self, **kwargs):
        context = super(TournamentDetailView, self).get_context_data(**kwargs)
        tournament = context.get(self.context_object_name)

        players = tournament.sort_players()
        for player in players:
            player.score = tournament.get_player_summary_score(player)

        context.update(players=players)
        return context
