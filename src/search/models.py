# search/models.py
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.db import models

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class SearchConfig(models.Model):
    """Конфигурация панели поиска"""

    if TYPE_CHECKING:
        fields: RelatedManager[SearchField]

    PANEL_POSITIONS = [
        ("top", "Верхняя панель"),
        ("left", "Левая боковая панель"),
        ("right", "Правая боковая панель"),
        ("bottom", "Нижняя панель"),
        ("modal", "Модальное окно"),
    ]

    name = models.CharField("Название конфигурации", max_length=100)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, verbose_name="Тип объекта для поиска"
    )
    position = models.CharField(
        "Расположение панели", max_length=10, choices=PANEL_POSITIONS, default="top"
    )
    is_active = models.BooleanField("Активна", default=True)
    placeholder = models.CharField(
        "Подсказка в поле", max_length=200, default="Поиск..."
    )
    show_results_count = models.BooleanField(
        "Показывать кол-во результатов", default=True
    )
    results_limit = models.PositiveIntegerField("Лимит результатов", default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Конфигурация поиска"
        verbose_name_plural = "Конфигурации поиска"

    def __str__(self):
        return f"{self.name} - {self.content_type}"


class SearchField(models.Model):
    """Поля для поиска"""

    FIELD_TYPES = [
        ("text", "Текстовое поле"),
        ("date_range", "Дата"),
        ("range", "Интервал чисел"),
        ("select", "Одинарный выбор"),
        ("select_multiple", "Множественный выбор"),
    ]

    config = models.ForeignKey(
        SearchConfig,
        on_delete=models.CASCADE,
        related_name="fields",
        verbose_name="Конфигурация",
    )
    field_name = models.CharField("Название поля в модели", max_length=100)
    label = models.CharField("Отображаемое название", max_length=100)
    field_type = models.CharField(
        "Тип поля", max_length=100, choices=FIELD_TYPES, default="text"
    )
    is_visible = models.BooleanField("Отображать в форме", default=True)
    is_searchable = models.BooleanField("Использовать для поиска", default=True)
    is_required = models.BooleanField("Обязательное поле", default=False)
    placeholder = models.CharField("Подсказка", max_length=200, blank=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    # Для выпадающих списков и радиокнопок
    choices = models.TextField(
        "Варианты выбора (через запятую)",
        blank=True,
        help_text="Для select, radio и checkbox. Формат: значение1=Текст1, значение2=Текст2",
    )

    # Для диапазонов
    min_value = models.FloatField("Минимальное значение", null=True, blank=True)
    max_value = models.FloatField("Максимальное значение", null=True, blank=True)
    step = models.FloatField("Шаг", null=True, blank=True)

    class Meta:
        verbose_name = "Поле поиска"
        verbose_name_plural = "Поля поиска"
        ordering = ["order"]

    def __str__(self):
        return f"{self.label} ({self.field_name})"

    # не знаю может нужно випилить
    def get_choices_dict(self):
        """Преобразует строку choices в словарь"""
        if not self.choices:
            return {}

        result = {}
        for item in self.choices.split(","):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                result[key] = value
            else:
                result[item.strip()] = item.strip()
        return result
