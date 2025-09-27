from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


# Главная
def basket(request):
    # products = (
    #     Products.objects.select_related("category")
    #     .order_by('?')[:10]
    # )
    return render(request, "basket/basket.html")
