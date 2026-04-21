from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any, cast

from django.core.exceptions import FieldDoesNotExist
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from products.services import ProductPayloadBuilder
from .models import SearchConfig, SearchField


def _require_model_class(content_type: Any) -> type[models.Model]:
    model_class = content_type.model_class()
    if model_class is None:
        raise ValueError("content_type.model_class() returned None")
    return cast(type[models.Model], model_class)


def _objects[ModelT: models.Model](model_class: type[ModelT]) -> models.Manager[ModelT]:
    return cast(models.Manager[ModelT], cast(Any, model_class).objects)


def _parse_positive_int(
    value: Any,
    default: int,
    *,
    minimum: int = 1,
    maximum: int | None = None,
) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        parsed = default

    if parsed < minimum:
        parsed = minimum
    if maximum is not None and parsed > maximum:
        parsed = maximum
    return parsed


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _scalar(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        if not value:
            return None
        return value[-1]
    return value


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple, set)):
        return [v for v in value if not _is_blank(v)]
    if _is_blank(value):
        return []
    return [value]


def _extract_range_values(
    search_data: Mapping[str, Any], field_name: str
) -> tuple[Any, Any]:
    raw_value = search_data.get(field_name)
    if isinstance(raw_value, (list, tuple)):
        min_value = raw_value[0] if len(raw_value) > 0 else None
        max_value = raw_value[1] if len(raw_value) > 1 else None
        return min_value, max_value

    return search_data.get(f"{field_name}_min"), search_data.get(f"{field_name}_max")


def _parse_date(value: Any):
    if _is_blank(value):
        return None

    if isinstance(value, datetime):
        return value.date()

    text = str(value).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _build_query_from_search_data(search_fields, search_data: Mapping[str, Any]):
    query = Q()
    applied_filters: dict[str, Any] = {}

    for field in search_fields:
        field_name = field.field_name
        field_type = field.field_type
        raw_value = search_data.get(field_name)

        if field_type == "text":
            text_value = _scalar(raw_value)
            if _is_blank(text_value):
                continue
            text_value = str(text_value).strip()
            query &= Q(**{f"{field_name}__icontains": text_value})
            applied_filters[field_name] = text_value
            continue

        if field_type == "select":
            values = _as_list(raw_value)
            if not values:
                continue
            selected = values[-1]
            query &= Q(**{field_name: selected})
            applied_filters[field_name] = selected
            continue

        if field_type == "select_multiple":
            values = _as_list(raw_value)
            if not values:
                continue
            select_q = Q()
            for value in values:
                select_q |= Q(**{field_name: value})
            query &= select_q
            applied_filters[field_name] = values
            continue

        if field_type == "date_range":
            min_raw, max_raw = _extract_range_values(search_data, field_name)
            min_date = _parse_date(min_raw)
            max_date = _parse_date(max_raw)
            if min_date is None and max_date is None:
                continue
            if min_date is not None:
                query &= Q(**{f"{field_name}__gte": min_date})
            if max_date is not None:
                query &= Q(**{f"{field_name}__lte": max_date})
            applied_filters[field_name] = [
                str(min_raw).strip() if not _is_blank(min_raw) else None,
                str(max_raw).strip() if not _is_blank(max_raw) else None,
            ]
            continue

        if field_type == "range":
            min_raw, max_raw = _extract_range_values(search_data, field_name)
            if _is_blank(min_raw) and _is_blank(max_raw):
                continue
            if not _is_blank(min_raw):
                query &= Q(**{f"{field_name}__gte": min_raw})
            if not _is_blank(max_raw):
                query &= Q(**{f"{field_name}__lte": max_raw})
            applied_filters[field_name] = [
                min_raw if not _is_blank(min_raw) else None,
                max_raw if not _is_blank(max_raw) else None,
            ]

    return query, applied_filters


def _find_first_field(model_class: type[models.Model], candidates: list[str]) -> str | None:
    for name in candidates:
        try:
            model_class._meta.get_field(name)
        except FieldDoesNotExist:
            continue
        else:
            return name
    return None


def _get_ordering_options(model_class: type[models.Model]) -> list[dict[str, str]]:
    created_field = _find_first_field(
        model_class,
        ["created", "created_at", "publish", "published_at", "date_created"],
    )
    title_field = _find_first_field(model_class, ["title", "name"])
    price_field = _find_first_field(
        model_class,
        ["price", "discount_price", "sale_price", "cost", "amount"],
    )

    options: list[dict[str, str]] = []

    if created_field:
        options.extend(
            [
                {"value": f"-{created_field}", "label": "Сначала новые"},
                {"value": f"{created_field}", "label": "Сначала старые"},
            ]
        )

    if title_field:
        options.extend(
            [
                {"value": f"{title_field}", "label": "По названию (А–Я)"},
                {"value": f"-{title_field}", "label": "По названию (Я–А)"},
            ]
        )

    if price_field:
        options.extend(
            [
                {"value": f"{price_field}", "label": "По цене (сначала дешевле)"},
                {"value": f"-{price_field}", "label": "По цене (сначала дороже)"},
            ]
        )

    if not options:
        return [
            {"value": "-pk", "label": "Сначала новые (ID)"},
            {"value": "pk", "label": "Сначала старые (ID)"},
        ]

    return options


def _get_default_ordering(ordering_options: list[dict[str, str]]) -> str:
    return ordering_options[0]["value"]


def _render_cards_html(objects, request) -> str:
    html_chunks: list[str] = []
    for payload in objects:
        if _is_blank(payload.get("slug")):
            continue
        html_chunks.append(
            render_to_string(
                "modals/_product_card.html", {"object": payload}, request=request
            )
        )

    return "".join(html_chunks)


def _render_quick_view_html(objects, request) -> str:
    valid_objects = [payload for payload in objects if not _is_blank(payload.get("slug"))]
    return render_to_string("modals/_quick_view.html", {"objects": valid_objects}, request=request)


@require_POST
def api_search(request):
    """API endpoint для поиска товаров с HTML-блоками карточек и quick view."""

    try:
        data = cast(Mapping[str, Any], json.loads(request.body))
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Некорректный JSON"}, status=400
        )

    try:
        config_id = _parse_positive_int(data.get("config_id"), 0, minimum=0)
        content_type_id = _parse_positive_int(data.get("content_type_id"), 0, minimum=0)
        if config_id <= 0 or content_type_id <= 0:
            return JsonResponse(
                {
                    "success": False,
                    "message": "config_id и content_type_id обязательны",
                },
                status=400,
            )

        raw_search_data = data.get("search_data", {})
        search_data = (
            cast(Mapping[str, Any], raw_search_data)
            if isinstance(raw_search_data, Mapping)
            else {}
        )
        category_slug = (
            str(data.get("category_slug")).strip()
            if isinstance(data.get("category_slug"), str)
            else ""
        )

        config = SearchConfig.objects.get(
            id=config_id,
            content_type_id=content_type_id,
            is_active=True,
        )

        model_class = _require_model_class(config.content_type)
        search_fields = config.fields.filter(is_searchable=True)

        query, applied_filters = _build_query_from_search_data(search_fields, search_data)
        qs = _objects(model_class).filter(query)

        if category_slug:
            try:
                category_field = model_class._meta.get_field("category")
            except FieldDoesNotExist:
                pass
            else:
                related_model = cast(
                    type[models.Model] | None,
                    getattr(category_field, "related_model", None),
                )
                if related_model is not None:
                    try:
                        related_model._meta.get_field("slug")
                    except FieldDoesNotExist:
                        pass
                    else:
                        qs = qs.filter(category__slug=category_slug)
                        applied_filters["category_slug"] = category_slug

        try:
            model_class._meta.get_field("category")
        except FieldDoesNotExist:
            pass
        else:
            qs = qs.select_related("category")

        ordering_options = _get_ordering_options(model_class)
        allowed_ordering = {option["value"] for option in ordering_options}
        default_ordering = _get_default_ordering(ordering_options)

        raw_order_by = data.get("order_by")
        order_by = (
            raw_order_by
            if isinstance(raw_order_by, str) and raw_order_by in allowed_ordering
            else default_ordering
        )
        qs = qs.order_by(order_by)

        default_per_page = _parse_positive_int(
            data.get("limit"),
            int(config.results_limit),
            minimum=1,
            maximum=100,
        )
        per_page = _parse_positive_int(
            data.get("per_page"),
            default_per_page,
            minimum=1,
            maximum=100,
        )
        page_number = _parse_positive_int(data.get("page"), 1, minimum=1)

        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(page_number)
        product_payloads = ProductPayloadBuilder(request).build_many(
            list(page_obj.object_list)
        )
        cards_html = _render_cards_html(product_payloads, request=request)
        quick_view_html = _render_quick_view_html(product_payloads, request=request)

        return JsonResponse(
            {
                "success": True,
                "meta": {
                    "total": paginator.count,
                    "page": page_obj.number,
                    "per_page": per_page,
                    "has_next": page_obj.has_next(),
                    "has_prev": page_obj.has_previous(),
                },
                "ordering": {
                    "current": order_by,
                    "options": ordering_options,
                },
                "filters": applied_filters,
                "blocks": {
                    "cards_html": cards_html,
                    "quick_view_html": quick_view_html,
                },
            }
        )

    except SearchConfig.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Конфигурация поиска не найдена"},
            status=404,
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def get_field_choices(request, config_id, field_id):
    """Получение вариантов выбора для поля поиска."""
    try:
        field = SearchField.objects.get(id=field_id, config_id=config_id)
        model_class = _require_model_class(field.config.content_type)

        choices: list[dict[str, Any]] = []

        try:
            model_field = model_class._meta.get_field(field.field_name)

            raw_choices = getattr(model_field, "choices", None)
            if callable(raw_choices):
                raw_choices = raw_choices()

            if raw_choices:
                choices = [
                    {"value": choice[0], "label": choice[1]}
                    for choice in cast(Any, raw_choices)
                ]
            elif getattr(model_field, "related_model", None) is not None:
                related_model = cast(
                    type[models.Model] | None, getattr(model_field, "related_model")
                )
                if related_model is not None:
                    objects = _objects(related_model).all()[:100]
                    choices = [
                        {"value": getattr(obj, "id", obj.pk), "label": str(obj)}
                        for obj in objects
                    ]
            elif model_field.get_internal_type() == "BooleanField":
                choices = [
                    {"value": "true", "label": "Да"},
                    {"value": "false", "label": "Нет"},
                ]

            method_name = f"get_{field.field_name}_choices"
            if hasattr(model_class, method_name):
                method = getattr(model_class, method_name)
                custom_choices = method()
                if isinstance(custom_choices, (list, tuple)):
                    choices = [
                        {"value": choice[0], "label": choice[1]}
                        for choice in custom_choices
                    ]

        except Exception:
            fallback_choices = field.get_choices_dict()
            choices = [
                {"value": key, "label": label}
                for key, label in fallback_choices.items()
            ]

        return JsonResponse(
            {
                "success": True,
                "choices": choices,
                "model": str(model_class),
                "field_type": field.field_type,
            }
        )

    except SearchField.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Поле поиска не найдено"},
            status=404,
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
