# search/templatetags/search_tags.py
from __future__ import annotations

from collections.abc import Mapping

from django import template
from django.contrib.contenttypes.models import ContentType

from ..models import SearchConfig

register = template.Library()


@register.filter
def dict_get(obj, key):
    if obj is None or key is None:
        return ""

    # `QueryDict` and normal dict both implement `.get`.
    get = getattr(obj, "get", None)
    if callable(get):
        return get(key, "")

    if isinstance(obj, Mapping):
        return obj.get(key, "")

    return ""


@register.filter
def to_csv(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ",".join(str(v) for v in value if v not in (None, ""))
    return str(value)


@register.simple_tag
def should_expand_range(
    raw_min, raw_max, start_min, start_max, default_min, default_max
):
    def _s(value):
        if value is None:
            return ""
        return str(value)

    has_user_input = bool(raw_min) or bool(raw_max)
    if not has_user_input:
        return False

    return (_s(start_min) != _s(default_min)) or (_s(start_max) != _s(default_max))


@register.inclusion_tag("search/search_panel.html", takes_context=True)
def render_search_panel(context, config_name=None, content_type=None):
    """Рендерит панель поиска"""

    request = context.get("request")
    base_context = context.flatten()

    # Ищем конфигурацию
    config = None
    if config_name:
        try:
            config = SearchConfig.objects.get(name=config_name, is_active=True)
        except SearchConfig.DoesNotExist:
            pass

    # Или по content_type
    if not config and content_type:
        try:
            if isinstance(content_type, str):
                app_label, model = content_type.split(".")
                ct = ContentType.objects.get(app_label=app_label, model=model)
            else:
                ct = content_type
            config = SearchConfig.objects.filter(
                content_type=ct, is_active=True
            ).first()
        except (ValueError, ContentType.DoesNotExist):
            pass

    if not config:
        return {"config": None}

    # Получаем поля
    fields = config.fields.filter(is_visible=True).order_by("order")

    # Генерируем ID для формы
    form_id = f"search-form-{config.pk}"

    base_context.update(
        {
            "config": config,
            "fields": fields,
            "filters": context.get("filters", []),
            "form_id": form_id,
            "request": request,
        }
    )
    return base_context
