from __future__ import annotations

from typing import Any, cast

from django.core.exceptions import FieldDoesNotExist
from django.db import models

from .models import SearchField


class FieldChoices:
    """Сервис получения вариантов выбора (dropdown) для поля поиска."""

    def __init__(self, config_id: int, field_id: int) -> None:
        self.config_id = config_id
        self.field_id = field_id
        self._field: SearchField | None = None
        self._model_class: type[models.Model] | None = None

    def _load_field_and_model(self) -> None:
        """Ленивая загрузка и кэширование поля + модели."""
        if self._field is not None:
            return

        self._field = SearchField.objects.select_related("config__content_type").get(
            id=self.field_id, config_id=self.config_id
        )
        self._model_class = self._field.config.content_type.model_class()
        if not self._model_class:
            raise ValueError("Не удалось определить модель из content_type")

    def _require_field(self) -> SearchField:
        self._load_field_and_model()
        if self._field is None:
            raise ValueError("SearchField не загружен")
        return self._field

    def _require_model_class(self) -> type[models.Model]:
        self._load_field_and_model()
        if self._model_class is None:
            raise ValueError("Модель не определена")
        return cast(type[models.Model], self._model_class)

    def _resolve_field(self) -> models.Field:
        """Находит поле модели, поддерживает синтаксис `related__field`."""
        field = self._require_field()
        model_class = self._require_model_class()
        lookup = field.field_name
        if "__" not in lookup:
            return model_class._meta.get_field(lookup)

        parts = [p for p in lookup.split("__") if p]
        current: type[models.Model] = model_class
        for part in parts[:-1]:
            rel = current._meta.get_field(part)
            related_model = getattr(rel, "related_model", None)
            if related_model is None:
                raise FieldDoesNotExist(lookup)
            current = cast(type[models.Model], related_model)
        return current._meta.get_field(parts[-1])

    def _get_django_choices(
        self, model_field: models.Field
    ) -> list[dict[str, Any]] | None:
        raw = getattr(model_field, "choices", None)
        if callable(raw):
            raw = raw()
        return [{"value": c[0], "label": c[1]} for c in raw] if raw else None

    def _get_related_choices(
        self, model_field: models.Field
    ) -> list[dict[str, Any]] | None:
        related = getattr(model_field, "related_model", None)
        if not related:
            return None
        objs = related.objects.all()[:100]
        return [{"value": obj.pk, "label": str(obj)} for obj in objs]

    def _get_boolean_choices(
        self, model_field: models.Field
    ) -> list[dict[str, Any]] | None:
        if model_field.get_internal_type() == "BooleanField":
            return [
                {"value": "true", "label": "Да"},
                {"value": "false", "label": "Нет"},
            ]
        return None

    def _get_custom_choices(self) -> list[dict[str, Any]] | None:
        field = self._require_field()
        model_class = self._require_model_class()
        method_name = f"get_{field.field_name}_choices"
        if hasattr(model_class, method_name):
            result = getattr(model_class, method_name)()
            if isinstance(result, (list, tuple)):
                return [{"value": c[0], "label": c[1]} for c in result]
        return None

    def _get_fallback_choices(self) -> list[dict[str, Any]]:
        field = self._require_field()
        fallback = field.get_choices_dict()
        return [{"value": k, "label": v} for k, v in fallback.items()]

    def get_choices(self) -> dict[str, Any]:
        """Основной метод: возвращает структурированные варианты выбора."""
        field = self._require_field()
        model_class = self._require_model_class()
        model_field = self._resolve_field()

        choices = (
            self._get_django_choices(model_field)
            or self._get_related_choices(model_field)
            or self._get_boolean_choices(model_field)
            or self._get_custom_choices()
            or self._get_fallback_choices()
        )

        return {
            "choices": choices,
            "model": str(model_class),
            "field_type": field.field_type,
        }
