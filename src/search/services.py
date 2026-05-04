from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from django.core.exceptions import FieldDoesNotExist
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, QuerySet

from products.services import ProductPayloadBuilder

from .exceptions import (
    InvalidSearchRequestError,
    ModelResolutionError,
    SearchConfigNotFoundError,
)
from .models import SearchConfig, SearchField
from .renderers import SearchRenderer
from .forms import SearchRequestForm

logger = logging.getLogger(__name__)


def _parse_date(value: Any) -> date | None:
    if value is None or str(value).strip() == "":
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


class SearchQueryBuilder:
    """Инкапсулирует построение ORM-запроса с учётом динамических фильтров."""

    def __init__(
        self, model_class: type[models.Model], search_fields: QuerySet[SearchField]
    ):
        self.model_class = model_class
        self.search_fields = {f.field_name: f for f in search_fields}
        self.query = Q()
        self.applied_filters: dict[str, Any] = {}
        self._select_related: list[str] = []

    def _extract_range(
        self, search_data: dict[str, Any], field_name: str
    ) -> tuple[Any, Any]:
        raw = search_data.get(field_name)
        if isinstance(raw, (list, tuple)):
            min_val = raw[0] if len(raw) > 0 else None
            max_val = raw[1] if len(raw) > 1 else None
            return min_val, max_val
        return search_data.get(f"{field_name}_min"), search_data.get(
            f"{field_name}_max"
        )

    def _apply_filter(
        self, field_name: str, field_type: str, search_data: dict[str, Any]
    ) -> None:
        if field_type == "text":
            val = search_data.get(field_name)
            if isinstance(val, (list, tuple)):
                val = val[-1] if val else None
            if val is None or str(val).strip() == "":
                return
            val = str(val).strip()
            self.query &= Q(**{f"{field_name}__icontains": val})
            self.applied_filters[field_name] = val

        elif field_type == "select":
            val = search_data.get(field_name)
            if isinstance(val, (list, tuple)):
                val = val[-1] if val else None
            if val is None or str(val).strip() == "":
                return
            self.query &= Q(**{field_name: val})
            self.applied_filters[field_name] = val

        elif field_type == "select_multiple":
            val = search_data.get(field_name)
            vals = (
                [v for v in val if v is not None and str(v).strip() != ""]
                if isinstance(val, (list, tuple, set))
                else ([val] if val and str(val).strip() else [])
            )
            if not vals:
                return
            q = Q()
            for v in vals:
                q |= Q(**{field_name: v})
            self.query &= q
            self.applied_filters[field_name] = vals

        elif field_type in ("range", "date_range"):
            min_raw, max_raw = self._extract_range(search_data, field_name)
            if min_raw is None and max_raw is None:
                return

            if field_type == "date_range":
                min_val = _parse_date(min_raw)
                max_val = _parse_date(max_raw)
            else:
                min_val = (
                    min_raw
                    if min_raw is not None and str(min_raw).strip() != ""
                    else None
                )
                max_val = (
                    max_raw
                    if max_raw is not None and str(max_raw).strip() != ""
                    else None
                )

            if min_val is not None:
                self.query &= Q(**{f"{field_name}__gte": min_val})
            if max_val is not None:
                self.query &= Q(**{f"{field_name}__lte": max_val})

            self.applied_filters[field_name] = [
                str(min_raw).strip() if min_raw is not None else None,
                str(max_raw).strip() if max_raw is not None else None,
            ]

    def add_category_filter(self, category_slug: str | None) -> None:
        if not category_slug:
            return
        try:
            field = self.model_class._meta.get_field("category")
            related = getattr(field, "related_model", None)
            if related:
                related._meta.get_field("slug")
                self.query &= Q(category__slug=category_slug)
                self.applied_filters["category_slug"] = category_slug
                self._select_related.append("category")
        except FieldDoesNotExist:
            pass

    def build_queryset(self, search_data: dict[str, Any]) -> QuerySet:
        for field_name, field_config in self.search_fields.items():
            if not field_config.is_searchable:
                continue
            self._apply_filter(field_name, field_config.field_type, search_data)

        qs = self.model_class.objects.filter(self.query).distinct()
        if self._select_related:
            qs = qs.select_related(*list(set(self._select_related)))
        return qs


class SearchService:
    """Оркестратор поиска: конфиг → запрос → пагинация → ответ."""

    def __init__(self, request):
        self.request = request
        self.payload_builder = ProductPayloadBuilder(request)
        self.renderer = SearchRenderer(request)

    def execute(
        self,
        config_id: int,
        content_type_id: int,
        category_slug: str | None,
        search_data: dict[str, Any],
        order_by: str | None,
        page: int,
        per_page: int,
    ) -> dict[str, Any]:
        # Форма уже валидировала входные данные, ручные проверки диапазонов не нужны
        try:
            config = SearchConfig.objects.select_related("content_type").get(
                id=config_id, content_type_id=content_type_id, is_active=True
            )
        except SearchConfig.DoesNotExist:
            raise SearchConfigNotFoundError("Конфигурация поиска не найдена")

        model_class = config.content_type.model_class()
        if model_class is None:
            raise ValueError("Не удалось получить модель из content_type")

        search_fields = config.fields.filter(is_searchable=True)
        builder = SearchQueryBuilder(model_class, search_fields)
        builder.add_category_filter(category_slug)
        qs = builder.build_queryset(search_data)

        ordering = self._resolve_ordering(model_class, order_by)
        qs = qs.order_by(ordering)

        paginator = Paginator(qs, per_page)
        page_obj = paginator.get_page(page)

        payloads = self.payload_builder.build_many(list(page_obj.object_list))

        return {
            "success": True,
            "meta": {
                "total": paginator.count,
                "page": page_obj.number,
                "per_page": per_page,
                "has_next": page_obj.has_next(),
                "has_prev": page_obj.has_previous(),
            },
            "ordering": {
                "current": ordering,
                "options": self._get_ordering_options(model_class),
            },
            "filters": builder.applied_filters,
            "blocks": {
                "cards_html": self.renderer.render_cards(payloads),
                "quick_view_html": self.renderer.render_quick_view(payloads),
            },
        }

    def _resolve_ordering(
        self, model_class: type[models.Model], order_by: str | None
    ) -> str:
        options = self._get_ordering_options(model_class)
        valid = {o["value"] for o in options}
        return order_by if order_by in valid else options[0]["value"]

    def _get_ordering_options(
        self, model_class: type[models.Model]
    ) -> list[dict[str, str]]:
        def _find_first(candidates: list[str]) -> str | None:
            for name in candidates:
                try:
                    model_class._meta.get_field(name)
                    return name
                except FieldDoesNotExist:
                    continue
            return None

        created = _find_first(
            ["created", "created_at", "publish", "published_at", "date_created"]
        )
        title = _find_first(["title", "name"])
        price = _find_first(["price", "discount_price", "sale_price", "cost", "amount"])

        options: list[dict[str, str]] = []
        if created:
            options.extend(
                [
                    {"value": f"-{created}", "label": "Сначала новые"},
                    {"value": f"{created}", "label": "Сначала старые"},
                ]
            )
        if title:
            options.extend(
                [
                    {"value": f"{title}", "label": "По названию (А–Я)"},
                    {"value": f"-{title}", "label": "По названию (Я–А)"},
                ]
            )
        if price:
            options.extend(
                [
                    {"value": f"{price}", "label": "По цене (сначала дешевле)"},
                    {"value": f"-{price}", "label": "По цене (сначала дороже)"},
                ]
            )
        if not options:
            options = [
                {"value": "-pk", "label": "Сначала новые (ID)"},
                {"value": "pk", "label": "Сначала старые (ID)"},
            ]
        return options
