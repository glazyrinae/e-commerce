# search/views.py
from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any, cast

from django.core.exceptions import FieldDoesNotExist
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.http import JsonResponse, QueryDict
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST

from .models import SearchConfig, SearchField


def _require_model_class(content_type: Any) -> type[models.Model]:
    model_class = content_type.model_class()
    if model_class is None:
        raise ValueError("content_type.model_class() returned None")
    return cast(type[models.Model], model_class)


def _objects[ModelT: models.Model](model_class: type[ModelT]) -> models.Manager[ModelT]:
    return cast(models.Manager[ModelT], cast(Any, model_class).objects)


def _getattr(obj: Any, name: str, default: Any = None) -> Any:
    return getattr(obj, name, default)


class ListItems(View):
    def _find_first_field(
        self, model_class: type[models.Model], candidates: list[str]
    ) -> str | None:
        for name in candidates:
            try:
                model_class._meta.get_field(name)
            except FieldDoesNotExist:
                continue
            else:
                return name
        return None

    def _get_ordering_options(
        self, model_class: type[models.Model]
    ) -> list[dict[str, str]]:
        """
        Build ordering options based on actual fields of the model resolved via content_type.
        """
        created_field = self._find_first_field(
            model_class,
            ["created", "created_at", "publish", "published_at", "date_created"],
        )
        title_field = self._find_first_field(model_class, ["title", "name"])

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

        if not options:
            options = [
                {"value": "-pk", "label": "Сначала новые (ID)"},
                {"value": "pk", "label": "Сначала старые (ID)"},
            ]

        return options

    def _get_default_ordering(self, ordering_options: list[dict[str, str]]) -> str:
        return ordering_options[0]["value"]

    def _get_ordering(self, request, ordering_options: list[dict[str, str]]) -> str:
        """Определяет порядок сортировки из GET, валидируя по доступным опциям."""
        default_value = self._get_default_ordering(ordering_options)
        order_by = request.GET.get("order_by") or default_value
        allowed = {opt["value"] for opt in ordering_options}
        return order_by if order_by in allowed else default_value

    def _get_filtered_queryset(self, request):
        """Приватный метод: получает отфильтрованный queryset"""
        search_data = request
        filters = {}
        # Получаем конфигурацию
        config = SearchConfig.objects.get(is_active=True)
        # Получаем модель
        model_class = _require_model_class(config.content_type)
        # Строим запрос
        query = Q()
        search_fields = config.fields.filter(is_searchable=True)
        # Дополнительные фильтры
        for field in search_fields:
            field_name = field.field_name
            value = (
                search_data.getlist(field_name)
                if field.field_type == "select_multiple"
                else search_data.get(field_name)
            )
            filters.update({field_name: value})
            if not value and field.field_type not in ("date_range", "range"):
                continue

            if field.field_type == "text":
                field_lookup = f"{field_name}__icontains"
                query &= Q(**{field_lookup: value})

            elif field.field_type == "select":
                query &= Q(**{field_name: value})

            elif field.field_type == "select_multiple":
                if isinstance(value, list):
                    # OR запрос через | для каждого значения
                    select_q = Q()
                    for val in value:
                        select_q |= Q(**{field_name: val})
                    query &= select_q

            elif field.field_type == "date_range":
                if date_min := search_data.get(f"{field_name}_min"):
                    date_min_obj = datetime.strptime(date_min, "%d.%m.%Y").date()
                    query &= Q(**{f"{field_name}__gte": date_min_obj})
                    filters.update({f"{field_name}_min": date_min})
                if date_max := search_data.get(f"{field_name}_max"):
                    date_max_obj = datetime.strptime(date_max, "%d.%m.%Y").date()
                    query &= Q(**{f"{field_name}__lte": date_max_obj})
                    filters.update({f"{field_name}_max": date_max})

            elif field.field_type == "range":
                if rating_min := search_data.get(f"{field_name}_min"):
                    filters.update({f"{field_name}_min": rating_min})
                    query &= Q(**{f"{field_name}__gte": rating_min})
                if rating_max := search_data.get(f"{field_name}_max"):
                    filters.update({f"{field_name}_max": rating_max})
                    query &= Q(**{f"{field_name}__lte": rating_max})

        items = _objects(model_class).filter(query)
        return items, filters

    def _prepare_context(self, request, items, filters, ordering_options, order_by):
        """Подготавливает контекст для шаблона"""
        # Статистика
        total_items = len(items)
        order_by_label = next(
            (opt["label"] for opt in ordering_options if opt["value"] == order_by),
            order_by,
        )

        return {
            "items": items,
            "filters": filters,
            "total_items": total_items,
            "order_by": order_by,
            "order_by_label": order_by_label,
            "ordering_options": ordering_options,
        }

    def get(self, request, *args, **kwargs):
        """Обработка GET запроса"""
        # Используем свои методы
        items, filters = self._get_filtered_queryset(request.GET)

        model_class = cast(type[models.Model], items.model)
        ordering_options = self._get_ordering_options(model_class)
        order_by = self._get_ordering(request, ordering_options)

        # Сортировка
        items = items.order_by(order_by)

        # Пагинация
        page = request.GET.get("page", 1)
        paginator = Paginator(items, 3)

        try:
            items_page = paginator.page(page)
        except:  # noqa: E722
            items_page = paginator.page(1)

        # Подготавливаем контекст
        context = self._prepare_context(
            request, items_page, filters, ordering_options, order_by
        )
        context["items"] = items_page  # Обновляем items на пагинированные
        context["order_by"] = order_by
        # Обычный HTML вывод
        return render(request, "search/search_result.html", context)

    def post(self, request, *args, **kwargs):
        """
        PRG: POST -> Redirect -> GET.

        Builds a querystring from submitted form values and redirects to the same
        page so sorting/pagination work via URL without resubmitting POST.
        """
        q = QueryDict(mutable=True)

        for key, values in request.POST.lists():
            if key == "csrfmiddlewaretoken":
                continue
            cleaned = [v for v in values if v is not None and str(v).strip() != ""]
            if not cleaned:
                continue
            q.setlist(key, cleaned)

        # Always reset pagination when filters change.
        q.pop("page", None)

        base_url = reverse("search:search_result")
        query = q.urlencode()
        if query:
            return redirect(f"{base_url}?{query}")
        return redirect(base_url)


@require_POST
def api_search(request):
    """API endpoint для поиска"""

    try:
        data = cast(Mapping[str, Any], json.loads(request.body))
        config_id = data.get("config_id")
        content_type_id = data.get("content_type_id")
        search_data = cast(Mapping[str, Any], data.get("search_data", {}))
        limit = data.get("limit", 10)
        limit = int(limit)

        # Получаем конфигурацию
        config = SearchConfig.objects.get(
            id=config_id, content_type_id=content_type_id, is_active=True
        )

        # Получаем модель
        model_class = _require_model_class(config.content_type)

        # Строим запрос
        query = Q()
        search_fields = config.fields.filter(is_searchable=True)

        # Дополнительные фильтры
        for field in search_fields:
            field_name = field.field_name
            value = search_data.get(field_name)

            if not value and field.field_type != "date_range":
                continue

            if field.field_type == "text":
                field_lookup = f"{field_name}__icontains"
                query &= Q(**{field_lookup: value})

            # elif field.field_type == "checkbox":
            #     if value == "on" or value is True:
            #         query &= Q(**{field_name: True})
            #     elif value == "off" or value is False:
            #         query &= Q(**{field_name: False})

            elif field.field_type in ("select_multiple", "select"):
                if isinstance(value, list):
                    # OR запрос через | для каждого значения
                    select_q = Q()
                    for val in value:
                        select_q |= Q(**{field_name: val})
                    query &= select_q

            # elif field.field_type == "radio":
            #     query &= Q(**{field_name: value})

            # elif field.field_type == "number":
            #     query &= Q(**{field_name: value})

            elif field.field_type == "date_range":
                if date_min := search_data.get(f"{field_name}_min"):
                    date_min = datetime.strptime(date_min, "%d.%m.%Y").date()
                    query &= Q(**{f"{field_name}__gte": date_min})
                if date_max := search_data.get(f"{field_name}_max"):
                    date_max = datetime.strptime(date_max, "%d.%m.%Y").date()
                    query &= Q(**{f"{field_name}__lte": date_max})

            elif field.field_type == "range":
                if (
                    isinstance(value, (list, tuple))
                    and len(value) >= 2
                    and (value[0] or value[1])
                ):
                    if value[0]:
                        query &= Q(**{f"{field_name}__gte": value[0]})
                    if value[1]:
                        query &= Q(**{f"{field_name}__lte": value[1]})

        # Выполняем поиск
        qs = _objects(model_class).filter(query)
        _q = qs.query
        total = qs.count()
        results = list(qs[:limit])

        # Формируем ответ
        formatted_results = []
        for obj in results:
            get_absolute_url_name = "get_absolute_url"
            get_absolute_url = _getattr(obj, get_absolute_url_name)
            formatted_results.append(
                {
                    "id": getattr(obj, "id", obj.pk),
                    "content_type": f"{obj._meta.app_label}.{obj._meta.model_name}",
                    "title": str(obj),
                    "description": (
                        getattr(obj, "description", "")[:100]
                        if hasattr(obj, "description")
                        else ""
                    ),
                    "url": (get_absolute_url() if callable(get_absolute_url) else None),
                }
            )

        return JsonResponse(
            {
                "success": True,
                "query": str(_q),
                "results": formatted_results,
                "total": total,
                "has_more": total > limit,
                "show_count": config.show_results_count,
                "search_id": f"{config_id}_{content_type_id}",
            }
        )

    except SearchConfig.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Конфигурация поиска не найдена"}, status=404
        )

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def get_field_choices(request, config_id, field_id):
    """Получение вариантов выбора для поля из модели"""
    try:
        field = SearchField.objects.get(id=field_id, config_id=config_id)
        model_class = _require_model_class(field.config.content_type)

        choices = []

        # Получаем поле модели
        try:
            model_field = model_class._meta.get_field(field.field_name)

            choices_name = "choices"
            raw_choices = _getattr(model_field, choices_name)
            if callable(raw_choices):
                raw_choices = raw_choices()

            if raw_choices:
                choices = [
                    {"value": choice[0], "label": choice[1]}
                    for choice in cast(Any, raw_choices)
                ]
            # Если поле BooleanField
            # Если поле ForeignKey
            elif _getattr(model_field, "related_model", None) is not None:
                related_model_name = "related_model"
                related_model = cast(
                    type[models.Model] | None, _getattr(model_field, related_model_name)
                )
                if related_model is None:
                    raise ValueError("Field.related_model is None")
                # Берем все объекты или ограниченное количество
                objects = _objects(related_model).all()[:100]
                choices = [
                    {"value": getattr(obj, "id", obj.pk), "label": str(obj)}
                    for obj in objects
                ]

            # Если поле с choices (TextChoices или Choices)
            elif raw_choices:
                choices = [
                    {"value": choice[0], "label": choice[1]}
                    for choice in cast(Any, raw_choices)
                ]

            # Если поле BooleanField
            elif model_field.get_internal_type() == "BooleanField":
                choices = [
                    {"value": "true", "label": "Да"},
                    {"value": "false", "label": "Нет"},
                ]

            # Если в модели есть метод get_xxx_choices
            choices_method_name = f"get_{field.field_name}_choices"
            if hasattr(model_class, choices_method_name):
                choices_method = getattr(model_class, choices_method_name)
                custom_choices = choices_method()
                if isinstance(custom_choices, (list, tuple)):
                    choices = [
                        {"value": choice[0], "label": choice[1]}
                        for choice in custom_choices
                    ]

        except Exception:
            # Если не удалось получить из модели, используем сохраненные choices
            choices_dict = field.get_choices_dict()
            choices = [
                {"value": key, "label": label} for key, label in choices_dict.items()
            ]

        return JsonResponse(
            {
                "success": True,
                "choices": choices,
                "model": str(model_class),
                "field_type": field.field_type,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
