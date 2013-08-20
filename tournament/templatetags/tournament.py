from django import template

from ..models import Game

register = template.Library()


@register.filter
def side_score(obj, side):
    return obj.get_side_score(side) if isinstance(obj, Game) else None
