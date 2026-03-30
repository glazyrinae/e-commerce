import logging
from typing import TypedDict

from django.core.paginator import Paginator
from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from .models import Images, Products, Store

logger = logging.getLogger(__name__)


class ProductStoreItem(TypedDict):
    size: str
    cnt: int
    store_id: int


class ProductViewData(TypedDict):
    product: Products
    product_title: str
    product_category: str
    product_total_cnt: int
    store_items: list[Store]
    colors_grouped: dict[str, list[ProductStoreItem]]


# Главная
def list_items(request: HttpRequest) -> HttpResponse:
    products_qs = Products.get_random_with_details(10)  # это QuerySet
    products_list = list(products_qs)  # преобразуем в список
    available_products = get_products(products_list)  # теперь типы совпадают
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


def get_item(product: Products) -> dict:
    store_items = list(
        Store.objects.filter(product=product).select_related("color", "size")
    )

    # Группируем store по цветам для шаблона
    colors_grouped: dict[str, list[ProductStoreItem]] = {}
    for item in store_items:
        color = "Без цвета"
        if item.color and hasattr(item.color, "title"):
            color = item.color.title

        if color not in colors_grouped:
            colors_grouped[color] = []

        # Безопасное получение атрибутов
        size_value: str = "Не указан"
        if item.size and hasattr(item.size, "size"):
            size_value = str(item.size.size)

        colors_grouped[color].append(
            {"size": size_value, "cnt": item.cnt, "store_id": item.pk}
        )

    # Безопасное получение атрибутов продукта
    product_title = getattr(product, "title", "Без названия")
    category = getattr(product, "category", None)
    slug = getattr(category, "slug", None)
    category_title = getattr(category, "title", "Без категории")
    total_cnt = sum(getattr(item, "cnt", 0) for item in store_items)

    return {
        "product": product,
        "slug": slug,
        "product_title": product_title,
        "product_category": category_title,
        "product_total_cnt": total_cnt,
        "store_items": store_items,
        "colors_grouped": colors_grouped,
    }


def get_products(products: list[Products]) -> list[ProductViewData]:
    available_products: list[ProductViewData] = []
    for product in products:
        available_products.append(get_item(product))
    return available_products


def products(request: HttpRequest, category_slug: str) -> HttpResponse:
    items_per_page = 3
    page_number = request.GET.get("page", 1)

    products_qs = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )
    products_list = list(products_qs)
    available_products = get_products(products_list)
    paginator = Paginator(available_products, items_per_page)
    page_obj = paginator.get_page(page_number)

    # Проверяем AJAX запрос
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return load_more_content(request, category_slug)

    return render(request, "items/products.html", {"products": page_obj})


def load_more_content(request: HttpRequest, category_slug: str) -> JsonResponse:
    page_number = request.GET.get("page", 1)
    items_per_page = 3

    products_qs = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )

    products_list = list(products_qs)
    available_products = get_products(products_list)
    paginator = Paginator(available_products, items_per_page)
    page_obj = paginator.get_page(page_number)

    html_content = render_to_string(
        "items_partial.html",
        {"objects": page_obj},
        request=request,
    )

    return JsonResponse({"html": html_content, "has_next": page_obj.has_next()})


def product(request: HttpRequest, category_slug: str, product_id: int) -> HttpResponse:

    product = get_object_or_404(
        Products.objects.select_related("category"),
        category__slug=category_slug,
        id=product_id,
    )
    item = get_item(product)
    # Безопасное получение связанных объектов через менеджеры
    images: list[Images] = list(Images.objects.filter(product=product))
    item.update(
        {
            "images": images,
        }
    )

    return render(request, "detail.html", item)
