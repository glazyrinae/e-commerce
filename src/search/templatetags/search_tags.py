from __future__ import annotations

from typing import Any

from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from ..models import SearchConfig

register = template.Library()


def _resolve_search_config(
    config_name: str | None,
    content_type_input: str | ContentType | None,
) -> SearchConfig | None:
    """
    Находит активную SearchConfig по имени, content_type или возвращает последнюю созданную.
    Вынесено из тега для тестируемости и повторного использования.
    """
    qs = SearchConfig.objects.filter(is_active=True).select_related("content_type")

    if config_name:
        config = qs.filter(name=config_name).first()
        if config:
            return config

    if content_type_input:
        ct = None
        if isinstance(content_type_input, str):
            try:
                app_label, model_name = content_type_input.split(".", 1)
                ct = ContentType.objects.get(app_label=app_label, model=model_name)
            except (ValueError, ContentType.DoesNotExist):
                pass
        else:
            ct = content_type_input

        if ct:
            config = qs.filter(content_type=ct).first()
            if config:
                return config

    # Fallback: самая свежая активная конфигурация
    return qs.order_by("-id").first()


@register.filter
def dict_get(obj: Any, key: Any) -> Any:
    """Безопасный доступ к ключу словаря/QueryDict для шаблонов."""
    if obj is None or key is None:
        return ""
    get_method = getattr(obj, "get", None)
    if callable(get_method):
        return get_method(key, "")
    return ""


@register.filter
def to_csv(value: Any) -> str:
    """Преобразует список/кортеж/множество в строку через запятую."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ",".join(str(v) for v in value if v not in (None, ""))
    return str(value)


@register.simple_tag
def should_expand_range(
    raw_min: Any,
    raw_max: Any,
    start_min: Any,
    start_max: Any,
    default_min: Any,
    default_max: Any,
) -> bool:
    """Определяет, нужно ли разворачивать UI фильтра диапазона."""
    has_input = bool(raw_min) or bool(raw_max)
    if not has_input:
        return False

    # Сравниваем текущие значения со значениями по умолчанию
    return str(start_min) != str(default_min) or str(start_max) != str(default_max)


@register.inclusion_tag("search/search_panel.html", takes_context=True)
def render_search_panel(
    context,
    config_name: str | None = None,
    content_type: str | ContentType | None = None,
):
    """
    Рендерит панель поиска.
    Ожидает в контексте: request (для CSRF/i18n), filters (dict применённых фильтров).
    """
    config = _resolve_search_config(config_name, content_type)
    if not config:
        return {"config": None}

    fields = config.fields.filter(is_visible=True).order_by("order")
    form_id = f"search-form-{config.pk}"

    # Важно: для {% addtoblock %} внутри inclusion-template необходимо
    # прокинуть секizai holder из родительского контекста.
    result = {
        "config": config,
        "fields": fields,
        "filters": context.get("filters", {}),
        "form_id": form_id,
        "request": context.get("request"),
    }
    sekizai_varname = getattr(settings, "SEKIZAI_VARNAME", "SEKIZAI_CONTENT_HOLDER")
    sekizai_holder = context.get(sekizai_varname)
    if sekizai_holder is not None:
        result[sekizai_varname] = sekizai_holder
    return result
