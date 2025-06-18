from django import template
from django.utils.safestring import mark_safe
import markdown

register = template.Library()


@register.simple_tag
def get_discount(price: float, price_count: float) -> str:
    return f"{round((price - price_count) * 100 / price)} %"


@register.filter
def format_price(value):
    """Форматирует цену с пробелами между тысячами"""
    try:
        return "{:,.0f}".format(float(value)).replace(",", " ")
    except (ValueError, TypeError):
        return value


@register.filter(name="markdown")
def markdown_format(text):
    return mark_safe(markdown.markdown(text))


@register.filter(name="plural")
def choose_plural(amount: int, variants: list = ["отзыв", "отзыва", "отзывов"]) -> str:
    if isinstance(variants, list) and len(variants) == 3:
        if amount % 10 == 1 and amount % 100 != 11:
            variant = 0
        elif (
            amount % 10 >= 2
            and amount % 10 <= 4
            and (amount % 100 < 10 or amount % 100 >= 20)
        ):
            variant = 1
        else:
            variant = 2
        return f"{amount} {variants[variant]}"
    return ""
