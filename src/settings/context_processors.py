from .models import Settings, MenuItem

def site_settings(request):
    try:
        settings = Settings.objects.first()
    except Settings.DoesNotExist:
        settings = None
    
    url_parts = request.path.split("/")
    url_parts = [url_part for url_part in url_parts if url_part]
    active = url_parts[0] if len(url_parts) > 0 else "home"

    menu_items = MenuItem.objects.filter(is_active=True).order_by('order')
    
    return {
        "active": active,
        'site_settings': settings,
        'main_menu': menu_items,
    }