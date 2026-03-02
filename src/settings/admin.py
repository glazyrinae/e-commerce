from django.contrib import admin

from .models import MenuItem, Settings


@admin.register(Settings)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "phone_number", "email")

    def has_add_permission(self, request):
        # Разрешаем создать только одну запись настроек
        return not Settings.objects.exists()


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("title", "url_category", "order", "is_active")
    list_editable = ("order", "is_active")
