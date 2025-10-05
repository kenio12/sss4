from django import template
from game_maturi.models import MaturiGame

register = template.Library()

# @register.filter
# def is_user_entered(game, user):
#     """指定されたユーザーがこのゲームにエントリーしているかどうかをチェックするフィルタ"""
#     return game.is_user_entered(user)

@register.filter
def get_item(dictionary, key):
    """辞書からキーで値を取得するフィルター"""
    if dictionary is None:
        return None
    if not isinstance(dictionary, dict):
        return None
    
    # キーが文字列なら数値に変換を試みる
    if isinstance(key, str):
        try:
            key = int(key)
        except ValueError:
            pass
    
    print(f"Looking for key: {key} (type: {type(key)}) in dictionary with keys: {dictionary.keys()}")
    return dictionary.get(key)
