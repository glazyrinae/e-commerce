from django.shortcuts import render, get_object_or_404
from .models import Products
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


def list_items(request):
    return render(request, "items/list_items.html")


def product(request, category_slug, product_id):
    product = get_object_or_404(
        Products.objects.select_related("category"),
        category__slug=category_slug,
        id=product_id,
    )
    return render(request, "detail.html", {"product": product})


def products(request, category_slug):
    items_per_page = 6
    page_number = request.GET.get("page", 1)

    products = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )
    paginator = Paginator(products, items_per_page)
    page_obj = paginator.get_page(page_number)

    # Проверяем AJAX запрос
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return load_more_content(request, category_slug)

    return render(
        request, "items/products.html", {"products": page_obj, "page_obj": page_obj}
    )


def load_more_content(request, category_slug):
    page_number = request.GET.get("page", 1)
    items_per_page = 6  # Количество элементов на страницу

    # Ваш основной queryset (пример с продуктами)
    products = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )

    paginator = Paginator(products, items_per_page)
    page_obj = paginator.get_page(page_number)

    # Рендерим HTML для новых элементов
    html_content = render_to_string("ajax/items_partial.html", {"products": page_obj})

    return JsonResponse({"html": html_content, "has_next": page_obj.has_next()})
