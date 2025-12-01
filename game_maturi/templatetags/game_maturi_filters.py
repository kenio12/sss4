from django import template
import random
from datetime import timedelta
from game_maturi.models import MaturiGame

register = template.Library()


@register.filter
def add_days(date, days):
    """日付に指定日数を加算するフィルター"""
    if not date:
        return None
    try:
        return date + timedelta(days=int(days))
    except (ValueError, TypeError):
        return date

@register.filter
def filter_by_original_author(novels, author):
    """作者で小説をフィルタリングするカスタムフィルター"""
    if not novels:
        return []
    # リストの場合はリスト内包表記でフィルタリング
    return [novel for novel in novels if novel.original_author_id == author.id]

@register.filter
def get_item(dictionary, key):
    """辞書からキーで値を取得するフィルター"""
    if dictionary is None:
        return None
    if not isinstance(dictionary, dict):
        return None
    
    # キーを数値と文字列の両方で試す
    try:
        int_key = int(key)
        if int_key in dictionary:
            return dictionary[int_key]
    except (ValueError, TypeError):
        pass
    
    # 文字列キーでも試す
    str_key = str(key)
    print(f"Looking for key: {str_key} in dictionary with keys: {dictionary.keys()}")
    return dictionary.get(str_key)

@register.filter
def filter_published(novels):
    """公開済みの小説だけをフィルタリングするカスタムフィルター"""
    if not novels:
        return []
    return [novel for novel in novels if novel.status == 'published']

@register.filter
def shuffle(arg):
    tmp = list(arg)
    random.shuffle(tmp)
    return tmp 

@register.filter
def get_prediction(predictions, novel_id):
    """
    予想辞書から特定の小説IDに対応する予想を取得する
    
    Args:
        predictions: 予想の辞書 {novel_id: author_id}
        novel_id: 小説のID
    
    Returns:
        その小説に対する予想の作者ID、なければNone
    """
    if predictions and str(novel_id) in predictions:
        return predictions[str(novel_id)]
    return None 

@register.filter
def filter_by_predictor(all_predictions, predictor):
    """
    予想者でフィルタリング
    all_predictions: GamePredictionのQuerySet
    predictor: 予想者のUserオブジェクト
    """
    if not all_predictions or not predictor or not hasattr(predictor, 'id'):
        return []
    # 修正: all_predictionsの各要素のpredictor_idとpredictor.idを較
    return [p for p in all_predictions if hasattr(p, 'predictor_id') and p.predictor_id == predictor.id]

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def filter_by_game(predictions, game):
    """ゲームでフィルタリング"""
    return [p for p in predictions if p.maturi_game_id == game.id]

@register.filter
def filter_by_novel(predictions, novel):
    """特定の小説に対する予想を取得"""
    if isinstance(predictions, dict):
        return []
    return [p for p in predictions if p.novel_id == novel.id]

@register.filter
def filter_correct_predictions(predictions):
    """正解の予想のみをフィルタリング"""
    return [p for p in predictions if p.predicted_author_id == p.novel.original_author_id]

@register.filter
def count_correct_predictions_for_novel(predictions, novel):
    """特定の小説に対する正解数をカウント"""
    novel_predictions = [p for p in predictions if p.novel_id == novel.id]
    return sum(1 for p in novel_predictions 
              if p.predicted_author_id == p.novel.original_author_id)

@register.filter
def get_prediction_for_novel(predictions, novel):
    """特定の小説に対する予想を取得"""
    if not predictions:
        return None
    matching_predictions = [p for p in predictions if p.novel_id == novel.id]
    return matching_predictions[0] if matching_predictions else None

@register.filter
def get_prediction_result(prediction):
    """予想結果を○×-で返す"""
    if not prediction:
        return '-'
    if prediction.predicted_author_id == prediction.novel.original_author_id:
        return '○'
    return '×'

@register.filter
def subtract(value, arg):
    """引き算を行うフィルター"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def divide(value, arg):
    if float(arg) == 0:
        return 0
    return float(value) / float(arg)

@register.filter
def selectattr(sequence, attr):
    return [item for item in sequence if getattr(item, attr, None)]
