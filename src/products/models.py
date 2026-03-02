from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Categories(models.Model):
    """
    Модель категорий товаров.
    Используется для группировки обуви по типам (кроссовки, ботинки, туфли и т.д.)
    """

    title = models.CharField(
        max_length=250,
        unique=True,
        verbose_name="Название категории",
        help_text="Например: Кроссовки, Ботинки, Сандалии",
        db_comment="Название категории товаров (уникальное)",
    )
    desc = models.TextField(
        default="",
        verbose_name="Описание категории",
        help_text="Краткое описание для SEO и отображения на странице категории",
        db_comment="Текстовое описание категории для SEO и отображения",
    )
    slug = models.SlugField(
        max_length=250,
        default=None,
        verbose_name="URL-идентификатор",
        help_text="Человекопонятный URL на основе названия (напр. 'krossovki-nike')",
        db_comment="URL-идентификатор для формирования ЧПУ",
    )

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["title"])]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        db_table_comment = "Таблица категорий товаров для группировки обуви по типам"

    def __str__(self):
        return self.title


class Colors(models.Model):
    """
    Модель цветов обуви.
    Содержит доступные цвета для товаров (красный, синий, черный и т.д.)
    """

    title = models.CharField(
        max_length=250,
        unique=True,
        verbose_name="Название цвета",
        help_text="Например: Красный, Синий, Черный",
        db_comment="Название цвета обуви (уникальное)",
    )

    class Meta:
        verbose_name = "Цвет"
        verbose_name_plural = "Цвета"
        db_table_comment = "Таблица доступных цветов обуви"

    def __str__(self):
        return self.title


class Sizes(models.Model):
    """
    Модель размеров обуви.
    Содержит доступные размеры (35, 36, 37 и т.д.)
    """

    size = models.SmallIntegerField(
        unique=True,
        verbose_name="Размер обуви",
        help_text="Размер по европейской сетке (EUR)",
        db_comment="Размер обуви по европейской сетке (уникальный)",
    )

    class Meta:
        verbose_name = "Размер"
        verbose_name_plural = "Размеры"
        ordering = ["size"]
        db_table_comment = "Таблица доступных размеров обуви (EUR)"

    def __str__(self):
        return f"{self.size}"


class Products(models.Model):
    """
    Основная модель товаров (обуви).
    Содержит все характеристики и метаданные о товаре.
    """

    # Константы с вариантами выбора для полей
    GENDERS = [
        ("male", "мужские"),
        ("female", "женские"),
        ("unisex", "универсальные"),
        ("kids", "детские"),
    ]

    SEASON = [
        ("winter", "зима"),
        ("summer", "лето"),
        ("autumn", "осень"),
        ("spring", "весна"),
        ("spring-summer", "весна-лето"),
        ("autumn-winter", "осень-зима"),
    ]

    SHOE_BRAND_CHOICES = [
        # Спортивные бренды
        ("nike", "Nike"),
        ("adidas", "Adidas"),
        ("puma", "Puma"),
        ("reebok", "Reebok"),
        ("new_balance", "New Balance"),
        ("asics", "ASICS"),
        ("under_armour", "Under Armour"),
        ("skechers", "Skechers"),
        ("demix", "Demix"),
        # Люксовые бренды
        ("gucci", "Gucci"),
        ("prada", "Prada"),
        ("louis_vuitton", "Louis Vuitton"),
        ("balenciaga", "Balenciaga"),
        ("dior", "Dior"),
        # Уличная мода
        ("vans", "Vans"),
        ("converse", "Converse"),
        ("timberland", "Timberland"),
        ("dr_martens", "Dr. Martens"),
        # Обувь для активного отдыха
        ("salomon", "Salomon"),
        ("merrell", "Merrell"),
        ("columbia", "Columbia"),
        ("the_north_face", "The North Face"),
        # Российские бренды
        ("ralf_ringer", "Ralf Ringer"),
        ("ecco", "ECCO"),
        ("bugatti", "Bugatti"),
        ("carlo_pazolini", "Carlo Pazolini"),
        # Детская обувь
        ("kapitoshka", "Капитошка"),
        ("kotofey", "Котофей"),
        ("antilopa", "Антилопа"),
        ("bartek", "Bartek"),
    ]

    UPPER_MATERIAL_CHOICES = [
        ("leather", "Натуральная кожа"),
        ("suede", "Замша"),
        ("nubuck", "Нубук"),
        ("textile", "Текстиль"),
        ("mesh", "Сетка (дышащий материал)"),
        ("synthetic", "Искусственная кожа"),
        ("knit", "Вязаный материал"),
        ("thermo", "Термополиуретан (TPU)"),
        ("rubber", "Резина/каучук"),
        ("pu", "Полиуретан (PU)"),
        ("eva", "Этиленвинилацетат (EVA)"),
        ("neoprene", "Неопрен"),
        ("goretex", "Мембрана Gore-Tex"),
        ("elastic", "Эластичные материалы"),
        ("combination", "Комбинированные материалы"),
    ]

    SOLE_MATERIAL_CHOICES = [
        ("tpr", "Термопластичная резина (TPR)"),
        ("pu", "Полиуретан (PU)"),
        ("eva", "Этиленвинилацетат (EVA)"),
        ("rubber", "Натуральный каучук/резина"),
        ("tpu", "Термополиуретан (TPU)"),
        ("pvc", "Поливинилхлорид (PVC)"),
        ("phylon", "Файлон (Phylon)"),
        ("phylite", "Файлайт (Phylite)"),
        ("compressed_rubber", "Прессованная резина"),
        ("carbon", "Карбоновая подошва"),
        ("microcellular", "Микропористая резина"),
        ("crepe", "Креповая подошва"),
        ("leather", "Кожаная подошва"),
        ("combination", "Комбинированная подошва"),
    ]

    MANUFACTURE_COUNTRY_CHOICES = [
        # Европа
        ("it", "Италия"),
        ("de", "Германия"),
        ("pt", "Португалия"),
        ("es", "Испания"),
        ("fr", "Франция"),
        ("uk", "Великобритания"),
        ("tr", "Турция"),
        # Азия
        ("cn", "Китай"),
        ("vn", "Вьетнам"),
        ("in", "Индия"),
        ("id", "Индонезия"),
        ("jp", "Япония"),
        ("kr", "Южная Корея"),
        # Америка
        ("us", "США"),
        ("br", "Бразилия"),
        ("mx", "Мексика"),
        # СНГ
        ("ru", "Россия"),
        ("by", "Беларусь"),
        # Другие
        ("za", "Южная Африка"),
        ("au", "Австралия"),
    ]

    # Основные поля товара
    title = models.CharField(
        max_length=250,
        default="",
        unique=True,
        verbose_name="Название товара",
        help_text="Полное название модели обуви",
        db_comment="Полное название модели обуви (уникальное)",
    )
    desc = models.TextField(
        default="",
        verbose_name="Описание товара",
        help_text="Подробное описание, характеристики, особенности модели",
        db_comment="Подробное текстовое описание товара",
    )
    slug = models.SlugField(
        max_length=250,
        default=None,
        verbose_name="URL-идентификатор",
        help_text="Уникальный URL для страницы товара",
        db_comment="URL-идентификатор для формирования ЧПУ страницы товара",
    )

    # Ценовые поля
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=None,
        verbose_name="Цена",
        help_text="Регулярная цена товара",
        db_comment="Регулярная цена товара (до 10 знаков, 2 знака после запятой)",
    )
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=None,
        verbose_name="Цена со скидкой",
        help_text="Акционная цена (если есть скидка)",
        db_comment="Цена со скидкой (если применяется)",
    )

    # Связи и характеристики
    category = models.ForeignKey(
        Categories,
        related_name="products",
        default=None,
        on_delete=models.CASCADE,
        verbose_name="Категория",
        help_text="Категория к которой относится товар",
        db_comment="Внешний ключ к таблице Categories",
    )
    country = models.CharField(
        max_length=32,
        choices=MANUFACTURE_COUNTRY_CHOICES,
        default="ru",
        verbose_name="Страна производитель",
        help_text="Страна, где произведен товар",
        db_comment="Код страны производителя",
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDERS,
        default="unisex",
        verbose_name="Пол",
        help_text="Для кого предназначена обувь",
        db_comment="Пол целевой аудитории (male/female/unisex/kids)",
    )
    brand = models.CharField(
        max_length=120,
        choices=SHOE_BRAND_CHOICES,
        default="nike",
        verbose_name="Бренд",
        help_text="Производитель/бренд обуви",
        db_comment="Код бренда производителя",
    )
    season = models.CharField(
        max_length=16,
        choices=SEASON,
        default="summer",
        verbose_name="Сезон",
        help_text="Рекомендуемый сезон для носки",
        db_comment="Сезон для которого рекомендуется обувь",
    )
    upper_material = models.CharField(
        max_length=20,
        choices=UPPER_MATERIAL_CHOICES,
        default="leather",
        verbose_name="Материал верха",
        help_text="Материал из которого сделан верх обуви",
        db_comment="Код материала верха обуви",
    )
    sole_material = models.CharField(
        max_length=20,
        choices=SOLE_MATERIAL_CHOICES,
        default="rubber",
        verbose_name="Материал подошвы",
        help_text="Материал из которого сделана подошва",
        db_comment="Код материала подошвы",
    )

    # Метаданные
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания",
        help_text="Когда товар был добавлен в каталог",
        db_comment="Дата и время добавления товара в каталог",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
        help_text="Когда информация о товаре обновлялась последний раз",
        db_comment="Дата и время последнего обновления информации о товаре",
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name="Активен",
        help_text="Отображать товар на сайте или нет",
        db_comment="Флаг для отображения товара (True - отображается на сайте)",
    )
    weight = models.SmallIntegerField(
        default=0,
        verbose_name="Вес (граммы)",
        help_text="Вес товара в граммах (для расчета доставки)",
        db_comment="Вес товара в граммах для расчета стоимости доставки",
    )
    product_number = models.CharField(
        max_length=250,
        unique=True,
        default=None,
        verbose_name="Артикул",
        help_text="Уникальный артикул товара (SKU)",
        db_comment="Уникальный артикул товара (SKU) для идентификации",
    )

    @property
    def get_path_image_thumbnail(self) -> str:
        """
        Возвращает путь к миниатюре главного изображения товара.
        Используется в списках товаров для компактного отображения.
        """
        # Через менеджер objects - всегда доступно
        thumbnail = (
            Images.objects.filter(product=self, image_type="main")
            .values_list("thumbnail", flat=True)
            .first()
        )
        return str(thumbnail) if thumbnail else "empty.png"

    @property
    def get_path_image_main(self) -> str:
        """
        Возвращает путь к главному изображению товара.
        Используется на детальной странице товара.
        """
        # Через менеджер objects - всегда доступно
        image = (
            Images.objects.filter(product=self, image_type="main")
            .values_list("image", flat=True)
            .first()
        )
        return str(image) if image else "empty.png"

    @classmethod
    def get_random_with_details(cls, count=10):
        """
        Возвращает случайные товары с предзагруженными связанными данными.
        Оптимизированный метод для главной страницы и каруселей.

        Args:
            count: количество товаров (по умолчанию 10)
        """
        return (
            cls.objects.select_related("category")  # Загружаем категорию одним JOIN
            .prefetch_related(
                models.Prefetch(
                    "store",  # Загружаем остатки на складе
                    queryset=Store.objects.select_related(
                        "color", "size"
                    ),  # С цветами и размерами
                )
            )
            .order_by("?")[:count]  # Случайная сортировка
        )

    class Meta:
        ordering = ["-created_at"]  # Сортировка по умолчанию: сначала новые
        indexes = [
            models.Index(fields=["id", "slug"]),  # Для быстрого поиска по URL
            models.Index(fields=["title"]),  # Для поиска по названию
            models.Index(fields=["-created_at"]),  # Для сортировки по дате
            models.Index(fields=["brand"]),  # Для фильтрации по бренду
            models.Index(fields=["category"]),  # Для фильтрации по категории
        ]
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        db_table_comment = (
            "Основная таблица товаров (обуви) с характеристиками и метаданными"
        )

    def __str__(self):
        return f"{self.title} ({self.brand})"


class Store(models.Model):
    """
    Модель складского учета.
    Связывает товар с конкретным цветом и размером, указывает количество.
    """

    color = models.ForeignKey(
        Colors,
        related_name="store",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Цвет",
        help_text="Цвет данного экземпляра товара",
        db_comment="Внешний ключ к таблице Colors (может быть NULL)",
    )
    size = models.ForeignKey(
        Sizes,
        related_name="store",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Размер",
        help_text="Размер данного экземпляра товара",
        db_comment="Внешний ключ к таблице Sizes (может быть NULL)",
    )
    product = models.ForeignKey(
        Products,
        related_name="store",
        default=None,
        on_delete=models.CASCADE,
        verbose_name="Товар",
        help_text="Связанный товар",
        db_comment="Внешний ключ к таблице Products",
    )
    cnt = models.SmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Количество",
        help_text="Доступное количество на складе (только положительное число)",
        db_comment="Доступное количество единиц товара на складе (только > 0)",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["color", "size", "product"],
                name="unique_variant_color_size_product",
                violation_error_message="Такая комбинация цвета, размера и товара уже существует",
            ),
            models.CheckConstraint(
                condition=models.Q(cnt__gt=0),
                name="cnt_positive",
                violation_error_message="Количество товара должно быть положительным",
            ),
        ]
        indexes = [
            models.Index(
                fields=["product", "color", "size"]
            ),  # Для быстрого поиска остатков
        ]
        verbose_name = "Остаток на складе"
        verbose_name_plural = "Остатки на складе"
        db_table_comment = "Таблица складского учета с остатками по цветам и размерам"

    def __str__(self):
        # Используем getattr с безопасными значениями по умолчанию
        color_title = getattr(self.color, "title", "Без цвета")
        size_value = getattr(self.size, "size", "Без размера")
        product_title = getattr(self.product, "title", "Без товара")
        return f"{product_title} - {color_title}, {size_value}р: {self.cnt} шт."


class Images(models.Model):
    """
    Модель изображений товара.
    Поддерживает основное изображение, дополнительные и миниатюры.
    """

    IMAGE_TYPE_CHOICES = [
        ("main", "Основное изображение"),
        ("secondary", "Дополнительное"),
        ("thumbnail", "Миниатюра"),
    ]

    image = models.ImageField(
        blank=True,
        upload_to="%Y/%m/%d/",
        verbose_name="Изображение",
        help_text="Оригинальное изображение товара",
        db_comment="Путь к оригинальному файлу изображения",
    )
    thumbnail = models.ImageField(
        upload_to="%Y/%m/%d/thumbnails",
        verbose_name="Миниатюра",
        help_text="Уменьшенная копия для списков товаров",
        db_comment="Путь к файлу миниатюры изображения",
    )
    product = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Товар",
        help_text="Товар, которому принадлежит изображение",
        db_comment="Внешний ключ к таблице Products",
    )
    image_type = models.CharField(
        max_length=10,
        choices=IMAGE_TYPE_CHOICES,
        default="secondary",
        verbose_name="Тип изображения",
        help_text="Назначение изображения (главное, дополнительное, миниатюра)",
        db_comment="Тип изображения: main - основное, secondary - дополнительное, thumbnail - миниатюра",
    )

    class Meta:
        ordering = ["product", "image_type"]
        indexes = [
            models.Index(
                fields=["product", "image_type"]
            ),  # Для быстрой загрузки изображений товара
        ]
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"
        db_table_comment = "Таблица изображений товаров с поддержкой разных типов (основное, доп., миниатюра)"

    def __str__(self):
        product_title = getattr(self.product, "title", "Без товара")
        # Получаем отображаемое значение напрямую из choices
        type_display = dict(self.IMAGE_TYPE_CHOICES).get(self.image_type)
        return f"Изображение для {product_title} ({type_display})"
