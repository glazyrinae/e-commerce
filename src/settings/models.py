from django.db import models
from django.utils.translation import gettext_lazy as _

from products.models import Categories


class Settings(models.Model):
    """Глобальные настройки сайта.

    Модель хранит единый набор параметров, которые используются в шаблонах и по всему
    проекту (через контекст-процессор).

    Поля:
        title: Отображаемое название сайта (используется, например, в <title> и шапке).
        site_logo: Логотип сайта (необязательный файл, хранится в `site_settings/`).
        footer_text: Текст в подвале сайта (может быть пустым).
        phone_number: Контактный телефон (строка, формат задаётся администратором).
        email: Контактный email.
        is_maintenance_mode: Флаг «режим обслуживания» для временного отключения сайта.
    """

    title = models.CharField(_("Название сайта"), max_length=100)
    site_logo = models.ImageField(
        _("Логотип"),
        upload_to="site_settings/",
        null=True,
        blank=True,
        help_text=_("Файл логотипа, который отображается в шапке сайта."),
        db_comment="Путь к файлу логотипа сайта (может быть NULL).",
    )
    description = models.TextField(
        _("Описание сайта"),
        blank=True,
        help_text=_(
            "Краткое описание сайта для отображения в шапке или других местах."
        ),
        db_comment="Краткое описание сайта для отображения в шапке или других местах.",
    )
    footer_text = models.TextField(
        _("Текст в подвале"),
        blank=True,
        help_text=_("Произвольный текст для отображения в подвале сайта."),
        db_comment="Текст, отображаемый в подвале сайта.",
    )
    phone_number = models.CharField(
        _("Телефон"),
        max_length=20,
        blank=True,
        help_text=_("Контактный номер телефона, отображаемый на сайте."),
        db_comment="Контактный номер телефона сайта.",
    )
    email = models.EmailField(
        _("Email"),
        blank=True,
        help_text=_("Контактный email, отображаемый на сайте."),
        db_comment="Контактный email сайта.",
    )
    is_maintenance_mode = models.BooleanField(
        _("Режим обслуживания"),
        default=False,
        help_text=_("Если включено — сайт может показывать страницу обслуживания."),
        db_comment="Флаг режима обслуживания сайта.",
    )

    class Meta:
        verbose_name = _("Настройка сайта")
        verbose_name_plural = _("Настройки сайта")
        db_table_comment = "Глобальные настройки сайта (название, контакты, режим обслуживания и т.п.)."

    def __str__(self):
        return self.title


class MenuItem(models.Model):
    """Пункт главного меню сайта.

    В текущей реализации пункт меню может быть связан с категорией товаров. Порядок
    отображения регулируется полем `order`, а видимость — флагом `is_active`.

    Поля:
        title: Название пункта меню, отображаемое пользователю.
        category: Категория, на которую ведёт пункт меню (может быть пустой).
        order: Порядок сортировки (меньше — выше/раньше в меню).
        is_active: Управляет показом пункта в меню без удаления записи.
    """

    title = models.CharField(
        _("Название"),
        max_length=50,
        help_text=_("Текст, который будет показан в меню."),
        db_comment="Название пункта меню.",
    )
    category = models.ForeignKey(
        Categories,
        related_name="settings_url",
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Категория"),
        help_text=_("Категория, на которую ведёт этот пункт меню."),
        db_comment="Внешний ключ к таблице Categories",
    )
    order = models.PositiveIntegerField(
        _("Порядок"),
        default=0,
        help_text=_("Порядок сортировки в меню (меньше — выше)."),
        db_comment="Порядок сортировки пункта меню.",
    )
    is_active = models.BooleanField(
        _("Активно"),
        default=True,
        help_text=_("Если выключено — пункт не отображается в меню."),
        db_comment="Флаг активности пункта меню.",
    )

    @property
    def url_category(self):
        """Возвращает `slug` связанной категории (если категория задана)."""
        return self.category.slug if self.category else None

    class Meta:
        verbose_name = _("Пункт меню")
        verbose_name_plural = _("Пункты меню")
        ordering = ["order"]
        db_table_comment = (
            "Пункты главного меню сайта (связь с категорией и порядок отображения)."
        )

    def __str__(self):
        return self.title
