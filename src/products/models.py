from django.db import models
from django.utils import timezone


class Categories(models.Model):
    title = models.CharField(max_length=250, unique=True)
    desc = models.TextField(default="")
    slug = models.SlugField(max_length=250, default=None)

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["title"])]
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self):
        return self.title


class Colors(models.Model):
    title = models.CharField(max_length=250, unique=True)

    def __str__(self):
        return self.title


class Sizes(models.Model):
    size = models.SmallIntegerField(unique=True)

    def __str__(self):
        return f"{self.size}"


class Products(models.Model):
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

    SOLE_MATERIAL_CHOICES = (
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
    )

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

    title = models.CharField(max_length=250, default="", unique=True)
    desc = models.TextField(default="")
    slug = models.SlugField(max_length=250, default=None)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=None)
    category = models.ForeignKey(
        Categories, related_name="products", default=None, on_delete=models.CASCADE
    )
    country = models.CharField(
        max_length=32,
        choices=MANUFACTURE_COUNTRY_CHOICES,
        default="ru",
        verbose_name="Страна производитель",
    )
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, default=None)
    gender = models.CharField(
        max_length=10, choices=GENDERS, default="unisex", verbose_name="Тип обуви"
    )
    brand = models.CharField(
        max_length=120, choices=SHOE_BRAND_CHOICES, default="nike", verbose_name="Брэнд"
    )
    season = models.CharField(
        max_length=16, choices=SEASON, default="summer", verbose_name="Сезон"
    )
    upper_material = models.CharField(
        max_length=20,
        choices=UPPER_MATERIAL_CHOICES,
        default="leather",
        verbose_name="Материал верха",
    )
    sole_material = models.CharField(
        max_length=20,
        choices=SOLE_MATERIAL_CHOICES,
        default="leather",
        verbose_name="Материал подошвы",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)
    weight = models.SmallIntegerField(default=0)
    product_number = models.CharField(max_length=250, unique=True, default=None)

    @property
    def get_path_image_thumbnail(self):
        """Список файлов"""
        return (
            self.images.filter(image_type="main")
            .values_list("thumbnail", flat=True)
            .first()
        ) or "empty.png"

    @property
    def get_path_image_main(self):
        """Список файлов"""
        return (
            self.images.filter(image_type="main")
            .values_list("image", flat=True)
            .first()
        ) or "empty.png"

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["id", "slug"]),
            models.Index(fields=["title"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.title


class Store(models.Model):
    
    color = models.ForeignKey(
        Colors, related_name="store", on_delete=models.SET_NULL, null=True
    )
    size = models.ForeignKey(
        Sizes, related_name="store", on_delete=models.SET_NULL, null=True
    )
    product = models.ForeignKey(
        Products, related_name="store", default=None, on_delete=models.CASCADE
    )
    cnt = models.SmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["color", "size", "product"],
                name="unique_variant_color_size_product",
            )
        ]

    def __str__(self):
        return "store"


class Images(models.Model):
    IMAGE_TYPE_CHOICES = [
        ("main", "Основное изображение"),
        ("secondary", "Дополнительное"),
        ("thumbnail", "Миниатюра"),
    ]

    image = models.ImageField(blank=True)
    thumbnail = models.ImageField(upload_to="%Y/%m/%d/thumbnails")
    product = models.ForeignKey(
        Products, on_delete=models.CASCADE, related_name="images"
    )

    image_type = models.CharField(
        max_length=10,
        choices=IMAGE_TYPE_CHOICES,
        default="secondary",
        verbose_name="Тип изображения",
    )
