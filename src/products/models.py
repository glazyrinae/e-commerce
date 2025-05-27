from django.db import models
from django.utils import timezone
# Create your models here.

class Categories(models.Model):
    title = models.CharField(max_length=250, unique=True)
    desc = models.TextField(default='')
    slug = models.SlugField(max_length=250, default=None)

    class Meta:
        ordering = ['title'] 
        indexes = [
            models.Index(fields = ['title'])
        ]
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        self.title
    

class Products(models.Model):

    GENDERS = [
        ("male", "мужские"),
        ("female", "женские"),
        ("unisex", "универсальные"),
        ("kids", "детские")
    ]

    title = models.CharField(max_length=250, default='', unique=True)
    desc = models.TextField(default='')
    slug = models.SlugField(max_length=250, default=None)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=None)
    category = models.ForeignKey(Categories, related_name='products', default=None, on_delete=models.CASCADE)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, default=None)
    gender = models.CharField(max_length=10,
        choices=GENDERS,
        default="unisex",
        verbose_name="Тип обуви")   
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)
    product_number =models.CharField(max_length=250, unique=True, default=None)

    class Meta:
        ordering = ['created_at'] 
        indexes = [
            models.Index(fields = ['id', 'slug']),
            models.Index(fields = ['title']),
            models.Index(fields = ['-created_at']),
        ]

    def __str__(self):
        self.title

class Images(models.Model):
    IMAGE_TYPE_CHOICES = [
        ("main", "Основное изображение"),
        ("secondary", "Дополнительное"),
        ("thumbnail", "Миниатюра"),
    ]

    image = models.ImageField(blank=True)
    thumbnail = models.ImageField(upload_to="%Y/%m/%d/thumbnails")
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="images")

    image_type = models.CharField(
        max_length=10,
        choices=IMAGE_TYPE_CHOICES,
        default="secondary",
        verbose_name="Тип изображения",
    )