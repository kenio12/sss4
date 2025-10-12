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
    'YYYY-MM' または 'YYYY' 形式の文字列を 'YYYY' 形式に変換
    例: '2025-09' → '2025', '2025' → '2025'
    date/datetime オブジェクトにも対応
    """
    if not value:
        return ''

    # 🔥 date/datetime オブジェクト対応
    if isinstance(value, (date, datetime)):
        return value.strftime('%Y')

    # 🔥 前後空白除去
    if isinstance(value, str):
        value = value.strip()

    try:
        # ハイフンがある場合は年のみ抽出、ない場合はそのまま返す
        if '-' in value:
            year, _ = value.split('-', 1)  # 最初のハイフンで分割
            return year
        else:
            # 年だけの場合はそのまま返す
            return value
    except (ValueError, AttributeError):
        # エラーが発生した場合は元の値を返す
        return value