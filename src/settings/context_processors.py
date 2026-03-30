from .models import MenuItem, Settings
from basket.models import Basket
from django.db.models import Sum


def site_settings(request):
    try:
        settings = Settings.objects.first()
    except Settings.DoesNotExist:
        settings = None

    url_parts = request.path.split("/")
    url_parts = [url_part for url_part in url_parts if url_part]
    active = url_parts[0] if len(url_parts) > 0 else "home"
    total_qty = 0
    if request.user.is_authenticated:
        total_qty = (
            Basket.objects.filter(user=request.user).aggregate(total=Sum("quantity"))[
                "total"
            ]
            or 0
        )

    menu_items = (
        MenuItem.objects.select_related("category")
        .filter(is_active=True)
        .order_by("order")
    )

    return {
        "active": active,
        "basket": total_qty,
        "site_settings": settings,
        "description": settings.description if settings else "",
        "title": settings.title if settings else "Мой магазин",
        "main_menu": menu_items,
    }
