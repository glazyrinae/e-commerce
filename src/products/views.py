import logging

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from .models import Products

logger = logging.getLogger(__name__)


# Главная
def list_items(request):
    products = Products.get_random_with_details(10)

    available_products = []
    for product in products:
        # Используем менеджер напрямую через _meta (Pylance не ругается)
        store_items = []
        try:
            # Прямой запрос к модели Store через менеджер
            from .models import Store

            store_items = list(
                Store.objects.filter(product=product).select_related("color", "size")
            )
        except (ImportError, Exception):
            store_items = []

        # Группируем store по цветам для шаблона
        colors_grouped = {}
        for item in store_items:
            color = "Без цвета"
            if item.color and hasattr(item.color, "title"):
                color = item.color.title

            if color not in colors_grouped:
                colors_grouped[color] = []

            # Безопасное получение атрибутов
            size_value = "Не указан"
            if item.size and hasattr(item.size, "size"):
                size_value = item.size.size

            colors_grouped[color].append(
                {"size": size_value, "cnt": item.cnt, "store_id": item.pk}
            )

        # Безопасное получение атрибутов продукта
        product_title = getattr(product, "title", "Без названия")
        category = getattr(product, "category", None)
        category_title = getattr(category, "title", "Без категории")
        total_cnt = sum(getattr(item, "cnt", 0) for item in store_items)

        available_products.append(
            {
                "product": product,
                "product_title": product_title,
                "product_category": category_title,
                "product_total_cnt": total_cnt,
                "store_items": store_items,
                "colors_grouped": colors_grouped,
            }
        )

    # Безопасные срезы
    featured = available_products[:5] if available_products else []
    latest = available_products[5:10] if len(available_products) > 5 else []

    return render(
        request,
        "items/list_items.html",
        {
            "featured_products": featured,
            "latest_products": latest,
        },
    )


def product(request, category_slug, product_id):
    # del request.session["cart"]
    product = get_object_or_404(
        Products.objects.select_related("category"),
        category__slug=category_slug,
        id=product_id,
    )

    # Безопасное получение связанных объектов через менеджеры
    images = []
    store_items = []

    try:
        from .models import Images, Store

        images = list(Images.objects.filter(product=product))
        store_items = list(
            Store.objects.filter(product=product).select_related("color", "size")
        )
    except (ImportError, Exception):
        pass

    # Безопасное получение цветов и размеров
    colors = set()
    sizes = set()

    for item in store_items:
        if item.color and hasattr(item.color, "title") and item.color.title:
            colors.add(item.color.title)
        if item.size and hasattr(item.size, "size") and item.size.size:
            sizes.add(str(item.size.size))

    return render(
        request,
        "detail.html",
        {
            "product": product,
            "images": images,
            "colors": colors,
            "sizes": sizes,
        },
    )


def products(request, category_slug):
    items_per_page = 5
    page_number = request.GET.get("page", 1)

    products_qs = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )
    paginator = Paginator(products_qs, items_per_page)
    page_obj = paginator.get_page(page_number)

    # Проверяем AJAX запрос
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return load_more_content(request, category_slug)

    return render(request, "items/products.html", {"products": page_obj})


# AJAX
def load_modal_content(request, category_slug):
    page_number = request.GET.get("page", 1)
    items_per_page = 5

    products_qs = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )

    paginator = Paginator(products_qs, items_per_page)
    page_obj = paginator.get_page(page_number)

    html_content = render_to_string("ajax/items_partial.html", {"products": page_obj})

    return JsonResponse({"html": html_content, "has_next": page_obj.has_next()})


def load_more_content(request, category_slug):
    page_number = request.GET.get("page", 1)
    items_per_page = 5

    products_qs = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )

    paginator = Paginator(products_qs, items_per_page)
    page_obj = paginator.get_page(page_number)

    html_content = render_to_string("ajax/items_partial.html", {"products": page_obj})

    return JsonResponse({"html": html_content, "has_next": page_obj.has_next()})
