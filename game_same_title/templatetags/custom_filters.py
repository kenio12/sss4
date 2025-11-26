from django import template
from dateutil.relativedelta import relativedelta

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def next_month(date_value):
    """翌月の日付を返すフィルタ（同タイトル提案は翌月用なので）"""
    if date_value:
        return date_value + relativedelta(months=1)
    return date_value 