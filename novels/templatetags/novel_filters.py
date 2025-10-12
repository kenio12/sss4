from django import template
from datetime import date, datetime

register = template.Library()

@register.filter
def modulo(value, arg):
    """Returns the remainder of value divided by arg"""
    return int(value) % int(arg)

@register.filter
def format_event_month(value):
    """
    'YYYY-MM' 形式の文字列を 'YYYY年M月' 形式に変換
    例: '2025-09' → '2025年9月'
    date/datetime オブジェクトにも対応
    """
    if not value:
        return ''

    # 🔥 date/datetime オブジェクト対応
    if isinstance(value, (date, datetime)):
        value = value.strftime('%Y-%m')

    # 🔥 前後空白除去
    if isinstance(value, str):
        value = value.strip()

    try:
        year, month = value.split('-')
        month_int = int(month)

        # 🔥 月の妥当性チェック (1-12)
        if not (1 <= month_int <= 12):
            return value  # 不正な月の場合は元の値を返す

        # 月の先頭の0を削除（09 → 9）
        month = str(month_int)
        return f"{year}年{month}月"
    except (ValueError, AttributeError):
        # エラーが発生した場合は元の値を返す
        return value