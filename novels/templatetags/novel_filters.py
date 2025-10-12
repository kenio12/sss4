from django import template

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
    """
    if not value:
        return ''

    try:
        year, month = value.split('-')
        # 月の先頭の0を削除（09 → 9）
        month = str(int(month))
        return f"{year}年{month}月"
    except (ValueError, AttributeError):
        # エラーが発生した場合は元の値を返す
        return value