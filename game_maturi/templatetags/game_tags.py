from django import template
from game_maturi.models import MaturiGame

register = template.Library()

# @register.simple_tag
# def is_user_entered(game, user):
#     if user is None or game is None:
#         return False  # ユーザーまたはゲームがNoneの場合は、すぐにFalseを返す
#     # ユーザーが特定のゲームにエントリーしているかどうかをチェック
#     return game.entrants.filter(id=user.id).exists()

# @register.filter(name='is_user_entered')
# def is_user_entered(game, user):
#     return game.entrants.filter(id=user.id).exists()
