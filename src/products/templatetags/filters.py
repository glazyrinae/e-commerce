from typing import cast

import markdown  # type: ignore[import-untyped]
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def get_discount(price: float, price_count: float) -> str:
    return f"{round((price - price_count) * 100 / price)} %"


@register.filter
def format_price(value: object) -> object:
    """Форматирует цену с пробелами между тысячами"""
    try:
        if isinstance(value, str | int | float):
            return f"{float(value):,.0f}".replace(",", " ")
        return value
    except (ValueError, TypeError):
        return value


@register.filter(name="markdown")
def markdown_format(text: str) -> str:
    rendered_html = cast(str, markdown.markdown(text))
    return cast(str, mark_safe(rendered_html))


DEFAULT_PLURAL_VARIANTS = ["отзыв", "отзыва", "отзывов"]


@register.filter(name="plural")
def choose_plural(
    amount: int, variants: list[str] | None = None
) -> str:
    variants = variants or DEFAULT_PLURAL_VARIANTS
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
