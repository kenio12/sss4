from django import template
from datetime import date, datetime
from django.utils import timezone

register = template.Library()


@register.filter
def get_display_author(novel):
    """
    祭り小説の場合、予想期間終了後は本当の作者（original_author）を返す
    それ以外はauthorを返す
    """
    # 🔥 祭りゲームとの関連があるかどうかで判定（novel.eventは使わない）
    if novel.original_author:
        # 祭りゲームを取得
        maturi_game = novel.maturi_games.first()
        if maturi_game:
            today = timezone.localtime(timezone.now()).date()
            # 予想期間が終了している場合は本当の作者を表示
            if today > maturi_game.prediction_end_date:
                return novel.original_author
    return novel.author

@register.filter
def modulo(value, arg):
    """Returns the remainder of value divided by arg"""
    return int(value) % int(arg)

@register.filter
def format_event_month(value):
    """
    年月フィールドの表示形式変換
    - 'YYYY-MM' → 'YYYY年M月'（同タイトルイベント用）
    - 'YYYY' → 'YYYY'（祭りイベント用）
    例: '2025-09' → '2025年9月', '2025' → '2025'
    date/datetime オブジェクトにも対応
    """
    if not value:
        return ''

    # 🔥 date/datetime オブジェクト対応
    if isinstance(value, (date, datetime)):
        return value.strftime('%Y年%-m月')  # %-m で月の先頭0を削除

    # 🔥 前後空白除去
    if isinstance(value, str):
        value = value.strip()

    try:
        # ハイフンがある場合は「YYYY年M月」に変換
        if '-' in value:
            year, month = value.split('-', 1)
            month_int = int(month)

            # 月の妥当性チェック (1-12)
            if not (1 <= month_int <= 12):
                return value  # 不正な月の場合は元の値を返す

            return f"{year}年{month_int}月"
        else:
            # 年だけの場合（祭りイベント）はそのまま返す
            return value
    except (ValueError, AttributeError):
        # エラーが発生した場合は元の値を返す
        return value