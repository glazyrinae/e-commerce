# search/admin.py
from django.contrib import admin

from .models import SearchConfig, SearchField


class SearchFieldInline(admin.TabularInline):
    model = SearchField
    extra = 1
    fields = (
        "field_name",
        "label",
        "field_type",
        "is_visible",
        "is_searchable",
        "is_required",
        "order",
    )
    ordering = ("order",)


@admin.register(SearchConfig)
class SearchConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "content_type", "position", "is_active", "results_limit")
    list_filter = ("position", "is_active", "content_type")
    search_fields = ("name",)
    inlines = [SearchFieldInline]
    fieldsets = (
        ("Основное", {"fields": ("name", "content_type", "is_active")}),
        (
            "Внешний вид",
            {
                "fields": (
                    "position",
                    "placeholder",
                    "show_results_count",
                    "results_limit",
                )
            },
        ),
    )


@admin.register(SearchField)
class SearchFieldAdmin(admin.ModelAdmin):
    list_display = (
        "config",
        "field_name",
        "label",
        "field_type",
        "is_visible",
        "is_searchable",
        "order",
    )
    list_filter = ("config", "field_type", "is_visible", "is_searchable")
    search_fields = ("field_name", "label")
