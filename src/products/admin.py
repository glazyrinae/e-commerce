from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import Categories, Images, Products


class ImageInline(admin.StackedInline):
    model = Images
    extra = 1
    readonly_fields = ("thumbnail_preview",)
    fields = ("image", "thumbnail_preview", "image_type")

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="350" height="200" />', obj.thumbnail.url
            )
        return "-"

    thumbnail_preview.short_description = "Thumbnail Preview"


@admin.register(Categories)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "desc", "slug"]
    search_fields = ["title"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Products)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "slug", "desc", "price", "discount_price", "is_active", "product_number"]
    list_filter = ["title", "created_at"]
    search_fields = ["title", "created_at", "price"]
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["category"]
    date_hierarchy = "created_at"
    ordering = ["title", "created_at"]
    inlines = [ImageInline]