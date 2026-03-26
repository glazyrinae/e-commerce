from django.contrib import admin

from .models import Basket


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "product",
        "size",
        "color",
        "quantity",
        "updated_at",
    )
    list_filter = ("user", "product", "size", "color", "updated_at")
    search_fields = ("user__username", "product__title")
    raw_id_fields = ("user", "product", "size", "color")
    ordering = ("-updated_at", "-id")
