from .models import Settings, MenuItem

def site_settings(request):
    try:
        settings = Settings.objects.first()
    except Settings.DoesNotExist:
        settings = None
    
    menu_items = MenuItem.objects.filter(is_active=True).order_by('order')
    
    return {
        'site_settings': settings,
        'main_menu': menu_items,
    }